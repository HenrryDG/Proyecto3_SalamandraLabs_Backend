from rest_framework import serializers
from .models import Empleado
import re

class EmpleadoSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = Empleado
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
