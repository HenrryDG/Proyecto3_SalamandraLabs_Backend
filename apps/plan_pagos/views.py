from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

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
	return Response({"mensaje": "Datos inválid"
	"os", "errores": serializer.errors}, status=400)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def plan_pagos_notificaciones(request):
    """Obtiene las notificaciones de plan de pagos con fecha de vencimiento en los próximos 7 días."""
    hoy = date.today()
    limite = hoy + timedelta(days=7)

    # Solo cuotas pendientes dentro del rango
    cuotas = PlanPago.objects.filter(
        estado="Pendiente", fecha_vencimiento__range=(hoy, limite)
    ).select_related("prestamo_solicitud_cliente")

    notificaciones = []

    for cuota in cuotas:
        cliente = cuota.prestamo.solicitud.cliente
        nombre_cliente = f"{cliente.nombre} {cliente.apellido_paterno or ''} {cliente.apellido_materno or ''}".strip()

        dias_restantes = (cuota.fecha_vencimiento - hoy).days

        # Construir Mensaje
        if dias_restantes == 0:
            mensaje = f"La cuota del préstamo de {nombre_cliente} vence hoy ({cuota.fecha_vencimiento})."
        elif dias_restantes == 1:
            mensaje = f"La cuota del préstamo de {nombre_cliente} vence mañana ({cuota.fecha_vencimiento})."
        else:
            mensaje = f"La cuota del préstamo de {nombre_cliente} vence en {dias_restantes} días ({cuota.fecha_vencimiento})."

        notificaciones.append(
            {
                "id_plan_pago": cuota.id,
                "id_prestamo": cuota.prestamo.id,
                "nombre_cliente": nombre_cliente,
                "mensaje": mensaje,
            }
        )

    return Response({"notificaciones": notificaciones})