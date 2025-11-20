from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from datetime import date, timedelta
from django.db.models import Q

from .models import PlanPago
from .serializers import PlanPagoSerializer
from .utils import actualizar_cuotas_vencidas


@extend_schema(responses={200: PlanPagoSerializer(many=True)})
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def listar_plan_pagos_por_prestamo(request, prestamo_id: int):
	"""Lista el plan de pagos de un préstamo y actualiza cuotas vencidas automáticamente."""
	try:
		planes = PlanPago.objects.filter(prestamo_id=prestamo_id).select_related('prestamo').order_by('fecha_vencimiento')
		# Actualizar estados/mora de las vencidas antes de responder
		actualizar_cuotas_vencidas(planes)
		serializer = PlanPagoSerializer(planes, many=True)
		return Response(serializer.data, status=200)
	except Exception as e:
		return Response({"mensaje": "Error al recuperar el plan de pagos", "error": str(e)}, status=500)


@extend_schema(request=PlanPagoSerializer, responses={200: PlanPagoSerializer})
@api_view(["PATCH", "PUT"])
@permission_classes([IsAuthenticated])
def actualizar_plan_pago(request, plan_id: int):
	"""Permite modificar el método de pago o marcar la cuota como pagada. Campos calculados son de solo lectura."""
	try:
		plan = PlanPago.objects.select_related('prestamo').get(id=plan_id)
	except PlanPago.DoesNotExist:
		return Response({"mensaje": "Plan de pago no encontrado"}, status=404)

	serializer = PlanPagoSerializer(plan, data=request.data, partial=True)
	if serializer.is_valid():
		try:
			serializer.save()
			return Response(serializer.data, status=200)
		except Exception as e:
			return Response({"mensaje": "Error al actualizar el plan de pago", "error": str(e)}, status=500)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def plan_pagos_notificaciones(request):
    """Notificaciones de cuotas próximas a vencer (7 días) y vencidas (mora)."""
    hoy = date.today()
    limite = hoy + timedelta(days=7)

    # Meses en español para formato legible
    meses_es = {
        1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
        7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
    }

    def formato_fecha(dt: date) -> str:
        return f"{dt.day} de {meses_es[dt.month]}"  # año omitido por ejemplo solicitado

    # Cuotas pendientes próximas + cuotas vencidas
    cuotas = PlanPago.objects.filter(
        Q(estado="Pendiente", fecha_vencimiento__range=(hoy, limite)) |
        Q(estado="Vencida")
    ).select_related("prestamo__solicitud__cliente").order_by("fecha_vencimiento")

    notificaciones = []

    for cuota in cuotas:
        cliente = cuota.prestamo.solicitud.cliente
        nombre_cliente = f"{cliente.nombre} {cliente.apellido_paterno or ''} {cliente.apellido_materno or ''}".strip()
        id_cuota = cuota.id  # No existe número de cuota explícito, usamos id
        dias_diff = (cuota.fecha_vencimiento - hoy).days
        fecha_fmt = formato_fecha(cuota.fecha_vencimiento)

        if cuota.estado == "Vencida":
            dias_mora = (hoy - cuota.fecha_vencimiento).days
            if dias_mora == 1:
                mensaje = f"La cuota N°{id_cuota} venció ayer, {fecha_fmt}."
            else:
                mensaje = f"La cuota N°{id_cuota} lleva {dias_mora} días vencida (venció el {fecha_fmt})."
            if cuota.mora_cuota > 0:
                mensaje += f" Mora acumulada: Bs {cuota.mora_cuota}."
        else:  # Pendiente futura
            if dias_diff == 0:
                mensaje = f"La cuota N°{id_cuota} vence hoy, {fecha_fmt}."
            elif dias_diff == 1:
                mensaje = f"La cuota N°{id_cuota} vence mañana, {fecha_fmt}."
            else:
                mensaje = f"La cuota N°{id_cuota} vence en {dias_diff} días, {fecha_fmt}."

        notificaciones.append({
            "id_plan_pago": cuota.id,
            "id_prestamo": cuota.prestamo.id,
            "nombre_cliente": nombre_cliente,
            "estado": cuota.estado,
            "mensaje": mensaje,
        })

    return Response({"notificaciones": notificaciones})
