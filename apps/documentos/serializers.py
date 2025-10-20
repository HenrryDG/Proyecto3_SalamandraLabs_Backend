from rest_framework import serializers  
from .models import Documento
import re

class DocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Documento
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']