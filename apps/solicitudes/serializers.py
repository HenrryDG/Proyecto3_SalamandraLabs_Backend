from rest_framework import serializers
from .models import SolicitudPrestamo
from apps.documentos.serializers import DocumentoSerializer

class SolicitudSerializer(serializers.ModelSerializer):
    empleado_nombre = serializers.StringRelatedField(source='empleado', read_only=True)
    cliente_nombre = serializers.StringRelatedField(source='cliente', read_only=True)

    cliente_ingreso_mensual = serializers.DecimalField(
        source='cliente.ingreso_mensual', max_digits=12, decimal_places=2, read_only=True
    )

    monto_aprobado = serializers.SerializerMethodField(read_only=True)
    plazo_meses = serializers.SerializerMethodField(read_only=True)
    fecha_plazo = serializers.SerializerMethodField(read_only=True)
    documentos = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SolicitudPrestamo
        fields = [
            'id',
            'empleado_nombre',
            'cliente_nombre',
            'cliente_ingreso_mensual',
            'monto_solicitado',
            'monto_aprobado',
            'plazo_meses',
            'proposito',
            'fecha_solicitud',
            'fecha_aprobacion',
            'fecha_plazo',
            'estado',
            'observaciones',
            'empleado',
            'cliente',
            'documentos',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'empleado_nombre',
            'cliente_nombre',
            'cliente_ingreso_mensual',
            'monto_aprobado',
            'plazo_meses',
            'fecha_plazo',
            'documentos',
        ]

    def get_monto_aprobado(self, obj):
        if hasattr(obj, 'prestamo') and obj.prestamo:
            return obj.prestamo.monto_aprobado
        return None
    
    def get_plazo_meses(self, obj):
        if hasattr(obj, 'prestamo') and obj.prestamo:
            return obj.prestamo.plazo_meses
        return None
    
    def get_fecha_plazo(self, obj):
        if hasattr(obj, 'prestamo') and obj.prestamo:
            return obj.prestamo.fecha_plazo
        return None
    
    def get_documentos(self, obj):
        documentos = obj.documentos.all()
        return DocumentoSerializer(documentos, many=True).data
    

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
