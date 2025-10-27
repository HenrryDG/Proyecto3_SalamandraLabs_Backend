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
                prestamos = Prestamo.objects.all()
            else:
                prestamos = Prestamo.objects.filter(
                    solicitud__empleado=empleado_logueado
                )
            serializer = PrestamoSerializer(prestamos, many=True)
            return Response(serializer.data, status=200)
        except Exception as e:
            return Response(
                {"mensaje": "Error al recuperar los préstamos", "error": str(e)},
                status=500,
            )