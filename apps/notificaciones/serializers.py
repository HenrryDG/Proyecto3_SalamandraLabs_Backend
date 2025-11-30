"""
Serializers para las notificaciones.
"""

from rest_framework import serializers


class NotificacionSerializer(serializers.Serializer):
    """Serializer para una notificación individual."""
    
    id = serializers.CharField(read_only=True)
    tipo = serializers.CharField(read_only=True)
    categoria = serializers.CharField(read_only=True)
    titulo = serializers.CharField(read_only=True)
    mensaje = serializers.CharField(read_only=True)
    
    cliente_id = serializers.IntegerField(read_only=True)
    solicitud_id = serializers.IntegerField(allow_null=True, read_only=True)
    prestamo_id = serializers.IntegerField(allow_null=True, read_only=True)
    plan_pago_id = serializers.IntegerField(allow_null=True, read_only=True)
    
    prioridad = serializers.CharField(read_only=True)
    estilo = serializers.CharField(read_only=True)
    fecha_generacion = serializers.DateTimeField(read_only=True)
    fecha_evento = serializers.DateField(allow_null=True, read_only=True)
    
    leida = serializers.BooleanField(read_only=True)
    datos_extra = serializers.DictField(read_only=True)


class ResumenNotificacionesSerializer(serializers.Serializer):
    """Serializer para el resumen de notificaciones."""
    
    total = serializers.IntegerField(read_only=True)
    urgentes = serializers.IntegerField(read_only=True)
    altas = serializers.IntegerField(read_only=True)
    requiere_atencion = serializers.BooleanField(read_only=True)
    tipos = serializers.DictField(read_only=True)


class ConfiguracionNotificacionSerializer(serializers.Serializer):
    """Serializer para la configuración de notificaciones."""
    
    dias_anticipacion_recordatorio = serializers.IntegerField()
    dias_anticipacion_urgente = serializers.IntegerField()
    dias_anticipacion_inmediato = serializers.IntegerField()
    mostrar_mora_desde_dias = serializers.IntegerField()
    intervalo_recordatorio_mora_dias = serializers.IntegerField()
    intervalo_actualizacion_cuotas = serializers.IntegerField()
