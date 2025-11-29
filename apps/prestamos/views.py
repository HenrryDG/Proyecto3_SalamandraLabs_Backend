from django.shortcuts import render

# Create your views here.
from rest_framework.response import Response
from rest_framework.decorators import (
    api_view,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from .models import Prestamo
from .serializers import PrestamoSerializer
from apps.clientes.models import Cliente
from drf_spectacular.utils import extend_schema


@extend_schema(
    methods=["POST"],
    request=PrestamoSerializer,
    responses={201: PrestamoSerializer},
)
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def prestamo_collection(request):
    # Listar todos los préstamos
    if request.method == "GET":
        try:
            empleado_logueado = request.user.empleado
            if empleado_logueado.rol == "Administrador":
                prestamos = Prestamo.objects.all().order_by('-created_at')
            else:
                prestamos = Prestamo.objects.filter(
                    solicitud__empleado=empleado_logueado
                ).order_by('-created_at')
            
            # Actualizar estado de préstamos según estado de sus cuotas
            for prestamo in prestamos:
                cuotas_qs = prestamo.plan_pagos.all()
                if not cuotas_qs.exists():
                    # Sin cuotas todavía: mantener estado actual
                    continue

                total = cuotas_qs.count()
                pagadas = cuotas_qs.filter(estado='Pagada').count()
                tiene_vencidas = cuotas_qs.filter(estado='Vencida').exists()
                nuevo_estado = prestamo.estado  # valor por defecto

                # 1. Todas pagadas -> Completado
                if pagadas == total:
                    nuevo_estado = 'Completado'
                # 2. Alguna vencida (y no todas pagadas) -> Mora
                elif tiene_vencidas:
                    nuevo_estado = 'Mora'
                # 3. Caso contrario -> En Curso (hay pendientes pero ninguna vencida)
                else:
                    nuevo_estado = 'En Curso'

                if nuevo_estado != prestamo.estado:
                    prestamo.estado = nuevo_estado
                    prestamo.save(update_fields=['estado'])
            
            serializer = PrestamoSerializer(prestamos, many=True)
            return Response(serializer.data, status=200)
        except Exception as e:
            return Response(
                {"mensaje": "Error al recuperar los préstamos", "error": str(e)},
                status=500,
            )

    # Crear un préstamo
    if request.method == "POST":
        serializer = PrestamoSerializer(data=request.data)
        if serializer.is_valid():
            try:
                prestamo = serializer.save()
                return Response(serializer.data, status=201)
            except Exception as e:
                return Response({
                    "mensaje": "Error al crear el préstamo", 
                    "error": str(e)
                }, status=500)
        return Response({
            "mensaje": "Error en los datos proporcionados",
            "errores": serializer.errors,
        }, status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def prestamos_por_cliente(request, cliente_id):
    """Lista todos los préstamos asociados a un cliente específico."""
    try:
        cliente = Cliente.objects.get(pk=cliente_id)
    except Cliente.DoesNotExist:
        return Response(
            {
                "mensaje": "Cliente no encontrado",
                "error": f"El cliente con ID {cliente_id} no existe",
            },
            status=404,
        )

    try:
        prestamos = Prestamo.objects.filter(solicitud__cliente=cliente).order_by('-created_at')
        serializer = PrestamoSerializer(prestamos, many=True)
        return Response(serializer.data, status=200)
    except Exception as e:
        return Response(
            {
                "mensaje": "Error al recuperar los préstamos del cliente",
                "detalles": str(e),
            },
            status=500,
        )
