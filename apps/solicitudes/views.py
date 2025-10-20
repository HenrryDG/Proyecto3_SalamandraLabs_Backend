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
from .utils import limpiar_texto, extraer_direccion_ocr


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
                solicitudes = SolicitudPrestamo.objects.all()
            else:
                solicitudes = SolicitudPrestamo.objects.filter(
                    empleado=empleado_logueado
                )
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


@api_view(["GET", "PUT", "PATCH"])
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


@api_view(["POST"])
def verificar_carnet(request):
    """
    Recibe:
      - texto: texto OCR
      - solicitud_id: id de la solicitud
      - tipo_documento (opcional, default 'DNI')
    Crea o actualiza un Documento según si coincide el carnet del cliente.
    """
    texto = request.data.get("texto", "")
    solicitud_id = request.data.get("solicitud_id")
    tipo_documento = request.data.get("tipo_documento", "DNI")

    try:
        # Obtener la solicitud y el cliente asociado
        solicitud = SolicitudPrestamo.objects.get(id=solicitud_id)
        cliente = solicitud.cliente

        # Comparar texto OCR con carnet del cliente
        verificado = cliente.carnet in texto

        # Buscar documento existente
        documento, creado = Documento.objects.get_or_create(
            solicitud=solicitud,
            tipo_documento=tipo_documento,
            defaults={
                "verificado": verificado,
                "archivo": None,
            },  # archivo se puede actualizar si se envía
        )

        # Si ya existía, actualizamos verificado
        if not creado:
            documento.verificado = verificado
            documento.save()

        return Response(
            {
                "id": documento.id,
                "tipo_documento": documento.tipo_documento,
                "archivo": documento.archivo.url if documento.archivo else None,
                "verificado": documento.verificado,
                "created_at": documento.created_at,
                "updated_at": documento.updated_at,
                "solicitud_id": documento.solicitud.id,
            }
        )

    except SolicitudPrestamo.DoesNotExist:
        return Response({"error": "Solicitud no encontrada"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["POST"])
def verificar_direccion(request):
    """
    Verifica si la dirección del cliente coincide parcialmente con el texto OCR.
    """
    texto_ocr = request.data.get("texto", "")
    solicitud_id = request.data.get("solicitud_id")
    tipo_documento = request.data.get("tipo_documento", "factura")

    try:
        solicitud = SolicitudPrestamo.objects.get(id=solicitud_id)
        cliente = solicitud.cliente

        # 1 Extraer dirección OCR
        direccion_ocr = extraer_direccion_ocr(texto_ocr)

        # 2 Limpiar y dividir textos
        direccion_cliente = limpiar_texto(cliente.direccion or "")
        direccion_ocr = limpiar_texto(direccion_ocr)
        partes_cliente = set(direccion_cliente.split())
        partes_ocr = set(direccion_ocr.split())

        # 3 Calcular similitud con Jaccard
        interseccion = partes_cliente & partes_ocr
        union = partes_cliente | partes_ocr
        similitud = len(interseccion) / len(union) if union else 0

        # 4 Verificado si similitud >= 0.6 (60%)
        verificado = similitud >= 0.6

        # 5 Guardar resultado
        documento, creado = Documento.objects.get_or_create(
            solicitud=solicitud,
            tipo_documento=tipo_documento,
            defaults={"verificado": verificado, "archivo": None},
        )

        if not creado:
            documento.verificado = verificado
            documento.save()

        return Response(
            {
                "id": documento.id,
                "direccion_cliente": partes_cliente,
                "direccion_ocr": partes_ocr,
                "similitud": round(similitud * 100, 2),
                "verificado": verificado,
            }
        )

    except SolicitudPrestamo.DoesNotExist:
        return Response({"error": "Solicitud no encontrada"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
