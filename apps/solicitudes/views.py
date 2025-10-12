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
from django.utils import timezone


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

@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def solicitud_element(request, pk):
    try:
        solicitud = SolicitudPrestamo.objects.get(pk=pk)
    except SolicitudPrestamo.DoesNotExist:
        return Response({
            'mensaje': 'Solicitud no encontrada',
            'error': f'La solicitud con ID {pk} no existe'
        }, status=404)

    # GET - Obtener una solicitud específica
    if request.method == 'GET':
        try:
            serializer = SolicitudSerializer(solicitud)
            return Response(serializer.data, status=200)
        except Exception as e:
            return Response({
                'mensaje': 'Error al procesar los datos de la solicitud',
                'detalles': str(e)
            }, status=500)

    # PUT - Actualizar datos de la solicitud
    elif request.method == 'PUT':
        serializer = SolicitudSerializer(solicitud, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=200)
            except Exception as e:
                return Response({
                    'mensaje': 'Error al guardar los cambios de la solicitud',
                    'detalles': str(e)
                }, status=500)
        return Response({
            'mensaje': 'Error en los datos proporcionados para actualizar',
            'errores': serializer.errors
        }, status=400)

    # PATCH - Cambiar el estado de la solicitud
    elif request.method == 'PATCH':
        try:
            nuevo_estado = request.data.get('estado')
            if nuevo_estado not in ['Pendiente', 'Aprobada', 'Rechazada']:
                return Response({
                    'mensaje': 'Estado inválido',
                    'error': "El estado debe ser 'Pendiente', 'Aprobada' o 'Rechazada'."
                }, status=400)

            solicitud.estado = nuevo_estado
            # Si se aprueba, registrar la fecha actual
            if nuevo_estado == 'Aprobada':
                solicitud.fecha_aprobacion = timezone.now().date()
            solicitud.save()

            return Response({
                'mensaje': f"Solicitud actualizada a estado '{nuevo_estado}'",
                'solicitud_id': pk,
                'estado': solicitud.estado,
                'fecha_aprobacion': solicitud.fecha_aprobacion
            }, status=200)
        except Exception as e:
            return Response({
                'mensaje': 'Error al modificar el estado de la solicitud',
                'detalles': str(e)
            }, status=500)