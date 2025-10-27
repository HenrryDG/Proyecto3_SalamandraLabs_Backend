from rest_framework import serializers
from .models import Prestamo
from datetime import timedelta, date
from dateutil.relativedelta import relativedelta
from apps.plan_pagos.models import PlanPago
from apps.plan_pagos.serializers import PlanPagoSerializer


class PrestamoSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.SerializerMethodField()
    plan_pagos = PlanPagoSerializer(many=True, read_only=True)

    class Meta:
        model = Prestamo
        fields = '__all__'
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'cliente_nombre',
            'monto_restante',
            'fecha_plazo',
            'estado',
            'plan_pagos',
        ]

    def get_cliente_nombre(self, obj):
        cliente = obj.solicitud.cliente
        return f"{cliente.nombre} {cliente.apellido_paterno or ''} {cliente.apellido_materno or ''}".strip()

    def validate_monto_aprobado(self, value):
        solicitud = self.initial_data.get('solicitud')
        if solicitud:
            solicitud_obj = self.fields['solicitud'].get_queryset().filter(id=solicitud).first()
            if solicitud_obj and value > solicitud_obj.monto_solicitado:
                raise serializers.ValidationError(
                    'El monto aprobado no puede ser mayor al monto solicitado.'
                )
        return value
   

    def validate(self, data):
        required_fields = ['solicitud', 'monto_aprobado', 'interes', 'fecha_desembolso']
        for field in required_fields:
            if not data.get(field):
                raise serializers.ValidationError(f"El campo '{field}' es requerido.")
        return data