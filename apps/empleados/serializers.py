from rest_framework import serializers
from .models import Empleado
import re
from django.contrib.auth.models import User

class EmpleadoSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = Empleado
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

# Validar formato de teléfono
    def validate_telefono(self, value):
        value_str = str(value)
        if not re.match(r'^[67]\d{7}$', value_str):
            raise serializers.ValidationError(
                "El teléfono debe tener 8 dígitos y comenzar con 6 o 7."
            )
        empleado_id = self.instance.id if self.instance else None
        if Empleado.objects.filter(telefono=value).exclude(id=empleado_id).exists():
            raise serializers.ValidationError("Este teléfono ya está registrado.")
        return value
    
    # Validar formato de correo electrónico
    def validate_correo(self, value):
        if not value:
            return value  # Permitir campos vacíos si el modelo lo permite
        empleado_id = self.instance.id if self.instance else None
        if Empleado.objects.filter(correo=value).exclude(id=empleado_id).exists():
            raise serializers.ValidationError("Este correo electrónico ya está registrado.")
        return value
    
    # Validar formato de username
    def validate_username(self, value):
        empleado_id = self.instance.id if self.instance else None
        if User.objects.filter(username=value).exists() and not self.instance:
            raise serializers.ValidationError("Este nombre de usuario ya está registrado.")
        return value
    
    # Validar campos requeridos
    def validate(self, data):
        required_fields = ['nombre', 'apellido_paterno', 'apellido_materno', 'telefono', 'rol']
        for field in required_fields:
            if not data.get(field):  
                raise serializers.ValidationError(f"El campo {field} es requerido.")
        # Solo validar username y password en creación, no en actualización
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
        # Crear empleado asociado al usuario
        empleado = Empleado.objects.create(user=user, **validated_data)
        return empleado
    
    def update(self, instance, validated_data):
        # Remover campos username y password si están presentes
        validated_data.pop('username', None)
        validated_data.pop('password', None)
        
        # Actualizar campos del empleado
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance