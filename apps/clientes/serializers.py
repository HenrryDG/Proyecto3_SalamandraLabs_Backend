from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Cliente
from apps.empleados.models import Empleado
import re

class ClienteSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Cliente
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "carnet": {"validators": []},
            "telefono": {"validators": []},
        }

    def validate_telefono(self, value):
        value_str = str(value)
        if not re.match(r"^[67]\d{7}$", value_str):
            raise serializers.ValidationError(
                "El teléfono debe tener 8 dígitos y comenzar con 6 o 7."
            )

        cliente_id = self.instance.id if self.instance else None

        # Verifica si ya existe en clientes (excepto el actual)
        existe_en_cliente = Cliente.objects.filter(telefono=value).exclude(id=cliente_id).exists()

        # Verifica si ya existe en empleados
        existe_en_empleado = Empleado.objects.filter(telefono=value).exists()

        if existe_en_cliente or existe_en_empleado:
            raise serializers.ValidationError("Este teléfono ya está registrado.")

        return value

    def validate_carnet(self, value):
        complemento = self.initial_data.get("complemento")
        cliente_id = self.instance.id if self.instance else None

        if not re.match(r"^\d{5,10}$", value):
            raise serializers.ValidationError("El carnet debe tener entre 5 y 10 dígitos.")

        existe = Cliente.objects.filter(carnet=value, complemento=complemento or None).exclude(id=cliente_id).exists()

        if existe:
            carnet_completo = f"{value}-{complemento}" if complemento else value
            raise serializers.ValidationError(f"El carnet {carnet_completo} ya está registrado.")

        return value

    def validate(self, data):
        required_fields = [
            "carnet", "nombre", "lugar_trabajo", "tipo_trabajo",
            "ingreso_mensual", "direccion", "telefono"
        ]
        for field in required_fields:
            if not data.get(field):
                raise serializers.ValidationError(f"El campo {field} es requerido.")

        # Validar username y password solo en creación
        if not self.instance:
            if not data.get('username'):
                raise serializers.ValidationError("El campo username es requerido.")
            if not data.get('password'):
                raise serializers.ValidationError("El campo password es requerido.")
        
        return data

    def create(self, validated_data):
        username = validated_data.pop('username')
        password = validated_data.pop('password')

        # Crear usuario en auth_user
        user = User.objects.create_user(
            username=username,
            password=password,
            is_active=True
        )

        # Crear cliente asociado al usuario
        cliente = Cliente.objects.create(user=user, **validated_data)
        return cliente

    def update(self, instance, validated_data):
        # No actualizar username ni password
        validated_data.pop('username', None)
        validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
