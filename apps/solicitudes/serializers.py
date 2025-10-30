from rest_framework import serializers
from .models import SolicitudPrestamo


class SolicitudSerializer(serializers.ModelSerializer):
    # Este se usa solo para mostrar el nombre (lectura)
    empleado_nombre = serializers.StringRelatedField(source='empleado', read_only=True)
    cliente_nombre = serializers.StringRelatedField(source='cliente', read_only=True)

    class Meta:
        model = SolicitudPrestamo
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'empleado_nombre', 'cliente_nombre']

    def validate_monto_solicitado(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "El monto solicitado debe ser un número positivo."
            )
        return value

    def validate(self, data):
        required_fields = ['cliente', 'monto_solicitado', 'proposito']
        for field in required_fields:
            if not data.get(field):
                raise serializers.ValidationError(f"El campo '{field}' es requerido.")
        return data
