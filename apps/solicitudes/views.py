from rest_framework.response import Response
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated

from apps.empleados.models import Empleado
from .models import SolicitudPrestamo
from apps.empleados.models import Empleado
from apps.clientes.models import Cliente
from apps.documentos.models import Documento
from .serializers import SolicitudSerializer
from drf_spectacular.utils import extend_schema
from django.utils import timezone
from ..documentos.utils import limpiar_texto, extraer_direccion_ocr


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
            empleado_logueado = request.user.empleado
            if empleado_logueado.rol == "Administrador":
                solicitudes = SolicitudPrestamo.objects.all().order_by('-created_at')
            else:
                solicitudes = SolicitudPrestamo.objects.filter(
                    empleado=empleado_logueado
                ).order_by('-created_at')
            serializer = SolicitudSerializer(solicitudes, many=True)
            return Response(serializer.data, status=200)
        except Exception as e:
            return Response(
                {"mensaje": "Error al recuperar las solicitudes", "error": str(e)},
                status=500,
            )

    # Crear una nueva solicitud
    # POST - Crear una nueva solicitud
    elif request.method == "POST":
        try:
            # Obtener el empleado autenticado
            empleado_logueado = request.user.empleado  # asumiendo OneToOne con User

            # Agregar el empleado a los datos del serializer
            data_con_empleado = {**request.data, "empleado": empleado_logueado.id}

            serializer = SolicitudSerializer(data=data_con_empleado)
            if serializer.is_valid():
                solicitud = serializer.save()
                return Response(serializer.data, status=201)
            else:
                return Response(
                    {
                        "mensaje": "Error en los datos proporcionados",
                        "errores": serializer.errors,
                    },
                    status=400,
                )

        except Exception as e:
            return Response(
                {"mensaje": "Error al crear la solicitud", "error": str(e)},
                status=500,
            )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def solicitudes_por_cliente(request, cliente_id):
    """Lista todas las solicitudes asociadas a un cliente específico."""
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
        solicitudes = SolicitudPrestamo.objects.filter(cliente=cliente).order_by('-created_at')
        serializer = SolicitudSerializer(solicitudes, many=True)
        return Response(serializer.data, status=200)
    except Exception as e:
        return Response(
            {
                "mensaje": "Error al recuperar las solicitudes del cliente",
                "detalles": str(e),
            },
            status=500,
        )


@api_view(["GET", "PUT", "DELETE", "PATCH"])
@permission_classes([IsAuthenticated])
def solicitud_element(request, pk):
    try:
        solicitud = SolicitudPrestamo.objects.get(pk=pk)
    except SolicitudPrestamo.DoesNotExist:
        return Response(
            {
                "mensaje": "Solicitud no encontrada",
                "error": f"La solicitud con ID {pk} no existe",
            },
            status=404,
        )

    # GET - Obtener una solicitud específica
    if request.method == "GET":
        try:
            serializer = SolicitudSerializer(solicitud)
            return Response(serializer.data, status=200)
        except Exception as e:
            return Response(
                {
                    "mensaje": "Error al procesar los datos de la solicitud",
                    "detalles": str(e),
                },
                status=500,
            )

    # PUT - Actualizar datos de la solicitud
    elif request.method == "PUT":
        serializer = SolicitudSerializer(solicitud, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=200)
            except Exception as e:
                return Response(
                    {
                        "mensaje": "Error al guardar los cambios de la solicitud",
                        "detalles": str(e),
                    },
                    status=500,
                )
        return Response(
            {
                "mensaje": "Error en los datos proporcionados para actualizar",
                "errores": serializer.errors,
            },
            status=400,
        )
    
    # DELETE - Eliminar una solicitud
    elif request.method == "DELETE":
        try:
            # Primero eliminar documentos asociados
            solicitud.documentos.all().delete()
            
            # Luego eliminar la solicitud
            solicitud.delete()
            
            return Response(
                {"mensaje": f"Solicitud con ID {pk} eliminada exitosamente."},
                status=200,
            )
        except Exception as e:
            return Response(
                {
                    "mensaje": "Error al eliminar la solicitud",
                    "detalles": str(e),
                },
                status=500,
            )


    # PATCH - Cambiar el estado de la solicitud
    elif request.method == "PATCH":
        try:
            nuevo_estado = request.data.get("estado")
            if nuevo_estado not in ["Pendiente", "Aprobada", "Rechazada"]:
                return Response(
                    {
                        "mensaje": "Estado inválido",
                        "error": "El estado debe ser 'Pendiente', 'Aprobada' o 'Rechazada'.",
                    },
                    status=400,
                )

            solicitud.estado = nuevo_estado

            solicitud.fecha_aprobacion = timezone.now().date()
            solicitud.save()

            return Response(
                {
                    "mensaje": f"Solicitud actualizada a estado '{nuevo_estado}'",
                    "solicitud_id": pk,
                    "estado": solicitud.estado,
                    "fecha_aprobacion": solicitud.fecha_aprobacion,
                },
                status=200,
            )
        except Exception as e:
            return Response(
                {
                    "mensaje": "Error al modificar el estado de la solicitud",
                    "detalles": str(e),
                },
                status=500,
            )
