from rest_framework import serializers
from .models import SolicitudPrestamo

class SolicitudSerializer(serializers.ModelSerializer):
    empleado_nombre = serializers.StringRelatedField(source='empleado', read_only=True)
    cliente_nombre = serializers.StringRelatedField(source='cliente', read_only=True)

    # Ingreso mensual del cliente (solo lectura)
    cliente_ingreso_mensual = serializers.DecimalField(
        source='cliente.ingreso_mensual', max_digits=12, decimal_places=2, read_only=True
    )

    # Monto aprobado del préstamo asociado (solo lectura, opcional)
    monto_aprobado = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SolicitudPrestamo
        fields = '__all__'
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'empleado_nombre',
            'cliente_nombre',
            'cliente_ingreso_mensual',
            'monto_aprobado',
        ]

    def get_monto_aprobado(self, obj):
        """Devuelve el monto aprobado si la solicitud tiene préstamo asociado"""
        if hasattr(obj, 'prestamo') and obj.prestamo:
            return obj.prestamo.monto_aprobado
        return None

    def validate_monto_solicitado(self, value):
        if value <= 0:
            raise serializers.ValidationError("El monto solicitado debe ser un número positivo.")
        return value

    def validate(self, data):
        required_fields = ['cliente', 'monto_solicitado', 'proposito']
        for field in required_fields:
            if not data.get(field):
                raise serializers.ValidationError(f"El campo '{field}' es requerido.")
        return data
