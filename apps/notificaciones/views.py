from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.clientes.models import Cliente
from .services import NotificacionService
from .serializers import (
    NotificacionSerializer,
    ResumenNotificacionesSerializer,
    ConfiguracionNotificacionSerializer,
)
from .types import ConfiguracionNotificacion, TipoNotificacion


TIPOS_PLAN_PAGOS = {
    TipoNotificacion.RECORDATORIO_CUOTA.value,
    TipoNotificacion.CUOTA_PROXIMA_VENCER.value,
    TipoNotificacion.CUOTA_VENCE_HOY.value,
    TipoNotificacion.CUOTA_VENCIDA.value,
}


@extend_schema(
    responses={200: NotificacionSerializer(many=True)},
    description="Obtiene las notificaciones de plan de pagos del cliente autenticado (recordatorios, cuotas próximas, vencidas).",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mis_notificaciones(request):
    """
    Obtiene las notificaciones de plan de pagos del cliente autenticado.
    """
    try:
        # Verificar si el usuario es un cliente
        cliente = Cliente.objects.get(user=request.user)
    except Cliente.DoesNotExist:
        return Response({
            "mensaje": "Usuario no es un cliente",
            "error": "Solo los clientes pueden ver sus notificaciones"
        }, status=403)
    
    try:
        service = NotificacionService()
        notificaciones = service.obtener_notificaciones_cliente(cliente.id)
        
        # Filtrar solo notificaciones de plan de pagos
        notificaciones_filtradas = [
            n for n in notificaciones 
            if n.tipo.value in TIPOS_PLAN_PAGOS
        ]
        
        # Convertir a diccionarios para la respuesta
        data = [n.to_dict() for n in notificaciones_filtradas]
        
        return Response({
            "total": len(data),
            "notificaciones": data
        }, status=200)
        
    except Exception as e:
        return Response({
            "mensaje": "Error al obtener notificaciones",
            "error": str(e)
        }, status=500)


@extend_schema(
    responses={200: NotificacionSerializer(many=True)},
    description="Obtiene las alertas emergentes del cliente autenticado.",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mis_alertas_emergentes(request):
    """
    Obtiene solo las notificaciones emergentes/alertas del cliente.
    """
    try:
        cliente = Cliente.objects.get(user=request.user)
    except Cliente.DoesNotExist:
        return Response({
            "mensaje": "Usuario no es un cliente",
            "error": "Solo los clientes pueden ver sus alertas"
        }, status=403)
    
    try:
        service = NotificacionService()
        alertas = service.obtener_notificaciones_emergentes(cliente.id)
        
        data = [n.to_dict() for n in alertas]
        
        return Response({
            "total": len(data),
            "alertas": data
        }, status=200)
        
    except Exception as e:
        return Response({
            "mensaje": "Error al obtener alertas",
            "error": str(e)
        }, status=500)


@extend_schema(
    responses={200: NotificacionSerializer(many=True)},
    description="Obtiene el historial de notificaciones del cliente.",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mi_historial_notificaciones(request):
    """
    Obtiene el historial/bandeja de notificaciones del cliente.
    """
    try:
        cliente = Cliente.objects.get(user=request.user)
    except Cliente.DoesNotExist:
        return Response({
            "mensaje": "Usuario no es un cliente",
            "error": "Solo los clientes pueden ver su historial"
        }, status=403)
    
    try:
        service = NotificacionService()
        historial = service.obtener_historial_notificaciones(cliente.id)
        
        data = [n.to_dict() for n in historial]
        
        return Response({
            "total": len(data),
            "notificaciones": data
        }, status=200)
        
    except Exception as e:
        return Response({
            "mensaje": "Error al obtener historial",
            "error": str(e)
        }, status=500)


@extend_schema(
    responses={200: ResumenNotificacionesSerializer},
    description="Obtiene un resumen de notificaciones del cliente.",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mi_resumen_notificaciones(request):
    """
    Obtiene un resumen de notificaciones del cliente.
    """
    try:
        cliente = Cliente.objects.get(user=request.user)
    except Cliente.DoesNotExist:
        return Response({
            "mensaje": "Usuario no es un cliente",
            "error": "Solo los clientes pueden ver su resumen"
        }, status=403)
    
    try:
        service = NotificacionService()
        resumen = service.obtener_resumen_notificaciones(cliente.id)
        
        return Response(resumen, status=200)
        
    except Exception as e:
        return Response({
            "mensaje": "Error al obtener resumen",
            "error": str(e)
        }, status=500)


# =============================================================================
# ENDPOINTS PARA EMPLEADOS/ADMINISTRADORES
# =============================================================================

@extend_schema(
    responses={200: NotificacionSerializer(many=True)},
    description="Obtiene las notificaciones de un cliente específico (solo empleados).",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notificaciones_cliente(request, cliente_id: int):
    """
    Obtiene todas las notificaciones de un cliente específico.
    """
    try:
        # Verificar que sea un empleado
        empleado = request.user.empleado
    except:
        return Response({
            "mensaje": "Acceso denegado",
            "error": "Solo empleados pueden acceder a este endpoint"
        }, status=403)
    
    # Verificar que el cliente exista
    try:
        cliente = Cliente.objects.get(pk=cliente_id)
    except Cliente.DoesNotExist:
        return Response({
            "mensaje": "Cliente no encontrado",
            "error": f"El cliente con ID {cliente_id} no existe"
        }, status=404)
    
    try:
        service = NotificacionService()
        notificaciones = service.obtener_notificaciones_cliente(cliente_id)
        
        data = [n.to_dict() for n in notificaciones]
        
        return Response({
            "cliente_id": cliente_id,
            "cliente_nombre": str(cliente),
            "total": len(data),
            "notificaciones": data
        }, status=200)
        
    except Exception as e:
        return Response({
            "mensaje": "Error al obtener notificaciones",
            "error": str(e)
        }, status=500)


@extend_schema(
    responses={200: ResumenNotificacionesSerializer},
    description="Obtiene el resumen de notificaciones de un cliente (solo empleados).",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def resumen_cliente(request, cliente_id: int):
    """
    Obtiene el resumen de notificaciones de un cliente específico.
    """
    try:
        empleado = request.user.empleado
    except:
        return Response({
            "mensaje": "Acceso denegado",
            "error": "Solo empleados pueden acceder a este endpoint"
        }, status=403)
    
    try:
        cliente = Cliente.objects.get(pk=cliente_id)
    except Cliente.DoesNotExist:
        return Response({
            "mensaje": "Cliente no encontrado",
            "error": f"El cliente con ID {cliente_id} no existe"
        }, status=404)
    
    try:
        service = NotificacionService()
        resumen = service.obtener_resumen_notificaciones(cliente_id)
        resumen["cliente_id"] = cliente_id
        resumen["cliente_nombre"] = str(cliente)
        
        return Response(resumen, status=200)
        
    except Exception as e:
        return Response({
            "mensaje": "Error al obtener resumen",
            "error": str(e)
        }, status=500)


@extend_schema(
    responses={200: NotificacionSerializer(many=True)},
    description="Obtiene todas las alertas del sistema para el dashboard.",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def alertas_dashboard(request):
    """
    Obtiene todas las alertas del sistema para el dashboard de administración.
    """
    try:
        empleado = request.user.empleado
    except:
        return Response({
            "mensaje": "Acceso denegado",
            "error": "Solo empleados pueden acceder al dashboard"
        }, status=403)
    
    try:
        service = NotificacionService()
        alertas = service.obtener_alertas_dashboard()
        
        data = [n.to_dict() for n in alertas]
        
        # Agrupar por cliente para mejor visualización
        por_cliente = {}
        for notif in data:
            cid = notif["cliente_id"]
            if cid not in por_cliente:
                por_cliente[cid] = {
                    "cliente_id": cid,
                    "notificaciones": []
                }
            por_cliente[cid]["notificaciones"].append(notif)
        
        return Response({
            "total_alertas": len(data),
            "clientes_afectados": len(por_cliente),
            "alertas": data,
            "por_cliente": list(por_cliente.values())
        }, status=200)
        
    except Exception as e:
        return Response({
            "mensaje": "Error al obtener alertas del dashboard",
            "error": str(e)
        }, status=500)


@extend_schema(
    responses={200: ConfiguracionNotificacionSerializer},
    description="Obtiene la configuración actual de notificaciones.",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def configuracion_notificaciones(request):
    """
    Obtiene la configuración actual del sistema de notificaciones.
    """
    try:
        config = ConfiguracionNotificacion()
        return Response(config.to_dict(), status=200)
    except Exception as e:
        return Response({
            "mensaje": "Error al obtener configuración",
            "error": str(e)
        }, status=500)
