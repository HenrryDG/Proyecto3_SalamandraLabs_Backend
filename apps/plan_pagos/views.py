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
	return Response({"mensaje": "Datos inválidos", "errores": serializer.errors}, status=400)
