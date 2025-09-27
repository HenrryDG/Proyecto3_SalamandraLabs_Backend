from rest_framework import serializers
from .models import Cliente
import re

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_telefono(self, value):
        if not re.match(r'^[67]\d{7}$', value):
            raise serializers.ValidationError(
                "El teléfono debe tener 8 dígitos y comenzar con 6 o 7."
            )
        cliente_id = self.instance.id if self.instance else None
        if Cliente.objects.filter(telefono=value).exclude(id=cliente_id).exists():
            raise serializers.ValidationError("Este teléfono ya está registrado.")
        
        return value
    
    def validate_carnet(self, value):
        if not re.match(r'^\d{5,10}$', value):
            raise serializers.ValidationError(
                "El carnet debe tener entre 5 y 10 dígitos."
            )
        cliente_id = self.instance.id if self.instance else None
        if Cliente.objects.filter(carnet=value).exclude(id=cliente_id).exists():
            raise serializers.ValidationError("Este carnet ya está registrado.")
        
        return value
    
    def validate(self, data):
        required_fields = ['carnet', 'nombre', 'apellido_paterno', 'apellido_materno','direccion', 
        'lugar_trabajo', 'tipo_trabajo', 'ingreso_mensual', 'direccion','telefono']
        for field in required_fields:
            if not data.get(field):  
                raise serializers.ValidationError(f"El campo {field} es requerido."
            )
        return data