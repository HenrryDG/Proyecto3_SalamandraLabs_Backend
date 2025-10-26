from rest_framework import serializers
from .models import Cliente
from apps.empleados.models import Empleado
import re


class ClienteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Cliente
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "carnet": {
                "validators": []
            },  # ← elimina el validador automático de unicidad
            "telefono": {"validators": []},
        }

    def validate_telefono(self, value):
        value_str = str(value)
        if not re.match(r"^[67]\d{7}$", value_str):
            raise serializers.ValidationError(
                "El teléfono debe tener 8 dígitos y comenzar con 6 o 7."
            )

        cliente_id = self.instance.id if self.instance else None

        # Verifica si el teléfono ya existe en clientes (excepto el actual)
        existe_en_cliente = (
            Cliente.objects.filter(telefono=value).exclude(id=cliente_id).exists()
        )

        # Verifica si el teléfono ya existe en empleados
        existe_en_empleado = Empleado.objects.filter(telefono=value).exists()

        if existe_en_cliente or existe_en_empleado:
            raise serializers.ValidationError("Este teléfono ya está registrado.")

        return value

    def validate_carnet(self, value):
        complemento = self.initial_data.get("complemento")  # se obtiene del request
        cliente_id = self.instance.id if self.instance else None

        # Validar formato básico
        if not re.match(r"^\d{5,10}$", value):
            raise serializers.ValidationError(
                "El carnet debe tener entre 5 y 10 dígitos."
            )

        # Construir carnet completo (por ejemplo: '123456-AB')
        carnet_completo = f"{value}-{complemento}" if complemento else value

        # Buscar coincidencias según ambos campos
        existe = Cliente.objects.filter(
            carnet=value,
            complemento=complemento or None
        ).exclude(id=cliente_id).exists()

        if existe:
            raise serializers.ValidationError(
                f"El carnet {carnet_completo} ya está registrado."
            )

        return value

    def validate(self, data):
        required_fields = [
            "carnet",
            "nombre",
            "direccion",
            "lugar_trabajo",
            "tipo_trabajo",
            "ingreso_mensual",
            "direccion",
            "telefono",
        ]
        for field in required_fields:
            if not data.get(field):
                raise serializers.ValidationError(f"El campo {field} es requerido.")
        return data
