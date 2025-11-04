from rest_framework import serializers
from .models import Prestamo
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from dateutil.relativedelta import relativedelta
from apps.plan_pagos.models import PlanPago
from apps.plan_pagos.serializers import PlanPagoSerializer
from apps.plan_pagos.utils import actualizar_cuotas_vencidas


class PrestamoSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.SerializerMethodField()
    plan_pagos = PlanPagoSerializer(many=True, read_only=True)

    monto_solicitado = serializers.SerializerMethodField()

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
            'monto_aprobado',
            'interes',
            'plan_pagos',
            'monto_solicitado',            
        ]

    def get_cliente_nombre(self, obj):
        cliente = obj.solicitud.cliente
        return f"{cliente.nombre} {cliente.apellido_paterno or ''} {cliente.apellido_materno or ''}".strip()

    def get_monto_solicitado(self, obj):
        return obj.solicitud.monto_solicitado
    
    def validate(self, data):
        required_fields = ['solicitud', 'fecha_desembolso']
        for field in required_fields:
            if not data.get(field):
                raise serializers.ValidationError(f"El campo '{field}' es requerido.")
        return data

    def create(self, validated_data):
        solicitud = validated_data['solicitud']
        cliente = solicitud.cliente
        fecha_desembolso = validated_data['fecha_desembolso']

        # --- 0. Verificar boleta de pago ---
        boleta = solicitud.documentos.filter(tipo_documento="Boleta de pago").first()
        if not boleta or not boleta.verificado:
            raise serializers.ValidationError(
                "No se puede crear préstamo: boleta de pago no verificada."
            )

        # --- 1. Porcentaje de endeudamiento según ingreso ---
        ingreso = Decimal(cliente.ingreso_mensual)
        if ingreso < 2300:
            porcentaje = Decimal('0.32')
        elif ingreso <= 3600:
            porcentaje = Decimal('0.34')
        elif ingreso <= 6000:
            porcentaje = Decimal('0.35')
        else:
            porcentaje = Decimal('0.40')

        # --- 2. Capacidad mensual de endeudamiento ---
        cuota_maxima = ingreso * porcentaje

        # --- 3. Interés según rango ---
        if ingreso <= 3600:
            interes = Decimal('1.5')  # 1.5% mensual
        elif ingreso <= 6000:
            interes = Decimal('1.3')
        else:
            interes = Decimal('1.1')

        # --- 4. Estimar plazo inicial ---
        monto_solicitado = Decimal(solicitud.monto_solicitado)
        plazo_meses = int((monto_solicitado / cuota_maxima).to_integral_value(rounding=ROUND_HALF_UP))
        plazo_meses = max(6, min(plazo_meses, 12))  # rango 6-12 meses

        # --- 5. Calcular monto aprobado según capacidad ---
        monto_aprobado = (cuota_maxima * plazo_meses / (1 + (interes / 100) * plazo_meses)).quantize(Decimal('0.01'))

        # --- 5b. Ajustar plazo si no alcanza monto solicitado ---
        while monto_aprobado < monto_solicitado and plazo_meses < 12:
            plazo_meses += 1
            monto_aprobado = (cuota_maxima * plazo_meses / (1 + (interes / 100) * plazo_meses)).quantize(Decimal('0.01'))

        # --- 5c. Nunca aprobar más del solicitado ---
        monto_aprobado = min(monto_aprobado, monto_solicitado)
        
        # --- 5d. Redondear monto aprobado a múltiplos de 100 ---
        monto_aprobado = (monto_aprobado / Decimal('100')).to_integral_value(rounding=ROUND_HALF_UP) * Decimal('100')

        # --- 6. Calcular monto restante con interés simple ---
        monto_restante = (monto_aprobado * (1 + (interes / 100) * plazo_meses)).quantize(Decimal('0.01'))

        # --- 7. Fecha de plazo ---
        fecha_plazo = fecha_desembolso + relativedelta(months=plazo_meses)

        # --- 8. Crear préstamo ---
        prestamo = Prestamo.objects.create(
            solicitud=solicitud,
            monto_aprobado=monto_aprobado,
            monto_restante=monto_restante,
            interes=interes,
            fecha_desembolso=fecha_desembolso,
            fecha_plazo=fecha_plazo,
            estado='En Curso',
            plazo_meses=plazo_meses
        )

        # --- 9. Generar plan de pagos ---
        monto_cuota = (monto_restante / plazo_meses).quantize(Decimal('0.01'))
        for i in range(plazo_meses):
            fecha_vencimiento = fecha_desembolso + relativedelta(months=i + 1)
            PlanPago.objects.create(
                prestamo=prestamo,
                fecha_vencimiento=fecha_vencimiento,
                monto_cuota=monto_cuota,
                mora_cuota=Decimal('0.00'),
                estado='Pendiente'
            )

        return prestamo
    
    def to_representation(self, instance):
        """Antes de serializar, refresca el estado/mora de cuotas vencidas."""
        try:
            actualizar_cuotas_vencidas(instance.plan_pagos.all())
        except Exception:
            # No bloquear la respuesta si ocurre algún error de actualización.
            pass
        return super().to_representation(instance)
