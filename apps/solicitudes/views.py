from rest_framework.response import Response
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from .models import SolicitudPrestamo
from .serializers import SolicitudSerializer
from drf_spectacular.utils import extend_schema


@extend_schema(
    methods=["POST"],
    request=SolicitudSerializer,
    responses={201: SolicitudSerializer},
)
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def solicitud_collection(request):
    # Listar todas las solicitudes
    if request.method == "GET":
        try:
            solicitudes = SolicitudPrestamo.objects.all()
            serializer = SolicitudSerializer(solicitudes, many=True)
            return Response(serializer.data, status=200)

        except Exception as e:
            return Response(
                {"mensaje": "Error al recuperar las solicitudes", "error": str(e)},
                status=500,
            )
        
    # Crear una nueva solicitud
    elif request.method == "POST":
        serializer = SolicitudSerializer(data=request.data)
        if serializer.is_valid():
            try:
                solicitud = serializer.save()
                return Response(serializer.data, status=201)
            except Exception as e:
                return Response(
                    {"mensaje": "Error al crear la solicitud", "error": str(e)},
                    status=500,
                )
        return Response(
            {"mensaje": "Error en los datos proporcionados", "errores": serializer.errors},
            status=400,
        )