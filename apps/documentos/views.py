from rest_framework.response import Response
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from .models import Documento
from apps.solicitudes.models import SolicitudPrestamo
from .serializers import DocumentoSerializer
from drf_spectacular.utils import extend_schema
from django.utils import timezone
from .utils import limpiar_texto, extraer_direccion_ocr
import re


@api_view(["GET"])
# @permission_classes([IsAuthenticated])
def documento_collection(request, solicitud_id):
    try:
        documentos = Documento.objects.filter(solicitud_id=solicitud_id)
        serializer = DocumentoSerializer(documentos, many=True)
        return Response(serializer.data, status=200)
    except Exception as e:
        return Response(
            {"mensaje": "Error al recuperar los documentos", "error": str(e)},
            status=500,
        )


@api_view(["POST"])
def verificar_carnet(request):
    """
    Recibe:
      - texto: texto OCR
      - solicitud_id: id de la solicitud
      - tipo_documento (opcional, default 'DNI')
    Crea o actualiza un Documento según si coincide el carnet (y complemento) del cliente.
    """
    texto = request.data.get("texto", "")
    solicitud_id = request.data.get("solicitud_id")
    tipo_documento = request.data.get("tipo_documento", "DNI")

    try:
        # Obtener la solicitud y el cliente asociado
        solicitud = SolicitudPrestamo.objects.get(id=solicitud_id)
        cliente = solicitud.cliente

        # Construir el carnet completo (ej: 123456-AB o 123456)
        carnet_completo = (
            f"{cliente.carnet}-{cliente.complemento}"
            if cliente.complemento
            else cliente.carnet
        )

        # Comparar texto OCR con carnet completo o solo carnet (por seguridad)
        verificado = carnet_completo in texto or cliente.carnet in texto

        # Buscar documento existente
        documento, creado = Documento.objects.get_or_create(
            solicitud=solicitud,
            tipo_documento=tipo_documento,
            defaults={
                "verificado": verificado,
                "archivo": None,
            },
        )

        # Si ya existía, actualizamos el estado de verificado
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
        return Response({"error": "Solicitud no encontrada."}, status=404)

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

        # 3 Calcular similitud
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


@api_view(["POST"])
def verificar_ingreso(request):
    """
    Verifica si el ingreso mensual del cliente coincide con la boleta OCR.
    Detecta el valor de ingreso buscando texto similar a 'Líquido pagable'.
    """
    texto_ocr = request.data.get("texto", "")
    solicitud_id = request.data.get("solicitud_id")
    tipo_documento = request.data.get("tipo_documento", "boleta_pago")

    try:
        solicitud = SolicitudPrestamo.objects.get(id=solicitud_id)
        cliente = solicitud.cliente

        # Regex flexible para "Líquido pagable" considerando comas, puntos y guiones OCR
        match = re.search(
            r"(?:L[ií]quido|LIQUIDO)\s*(?:\s+|[-—–]*)pagable\s*[:\-—–]?\s*([\d.,]+)",
            texto_ocr,
            re.IGNORECASE,
        )

        if match:
            ingreso_detectado = match.group(1)
            # Limpiar comas de miles, espacios y puntos duplicados
            ingreso_detectado = ingreso_detectado.replace(",", "").replace(" ", "")
            ingreso_detectado = re.sub(
                r"\.{2,}", ".", ingreso_detectado
            )  # reemplaza ".." por "."
            ingreso_detectado = float(ingreso_detectado)
        else:
            ingreso_detectado = 0

        ingreso_cliente = float(cliente.ingreso_mensual or 0)

        # Comparación con tolerancia del 10%
        verificado = False
        if ingreso_cliente > 0:
            diferencia = abs(ingreso_cliente - ingreso_detectado) / ingreso_cliente
            verificado = diferencia <= 0.1

        # Crear o actualizar Documento
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
                "tipo_documento": documento.tipo_documento,
                "ingreso_detectado": ingreso_detectado,
                "ingreso_cliente": ingreso_cliente,
                "verificado": verificado,
            }
        )

    except SolicitudPrestamo.DoesNotExist:
        return Response({"error": "Solicitud no encontrada"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
