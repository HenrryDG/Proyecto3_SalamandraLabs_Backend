from rest_framework import serializers
from .models import SolicitudPrestamo
import re


class SolicitudSerializer(serializers.ModelSerializer):

    empleado = serializers.StringRelatedField(read_only=True)
    cliente = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = SolicitudPrestamo
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_monto_solicitado(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "El monto solicitado debe ser un número positivo."
            )

    def validate(self, data):
        required_fields = [
            "empleado",
            "cliente",
            "monto_solicitado",
            "proposito",
            "plazo_meses",
        ]
        for field in required_fields:
            if not data.get(field):
                raise serializers.ValidationError(f"El campo '{field}' es requerido.")
        return data
