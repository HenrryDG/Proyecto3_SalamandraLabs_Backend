from rest_framework import serializers
from .models import PlanPago
from datetime import date

class PlanPagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanPago
        fields = '__all__'
        read_only_fields = [
            'id',
            'prestamo',
            'fecha_pago',
            'fecha_vencimiento',
            'monto_cuota',
            'mora_cuota',
            'created_at',
            'updated_at',
        ]

    def validate_metodo_pago(self, value):
        if value is None:
            return value
        if value not in ("QR", "Efectivo"):
            raise serializers.ValidationError("El método de pago debe ser 'QR' o 'Efectivo'.")
        return value

    def update(self, instance: PlanPago, validated_data):
        # Permitir cambiar solo 'metodo_pago' y/o marcar como 'Pagada'.
        metodo_pago = validated_data.get('metodo_pago', getattr(instance, 'metodo_pago', None))
        nuevo_estado = validated_data.get('estado')

        # Actualizar método de pago si fue enviado
        if 'metodo_pago' in validated_data:
            self.validate_metodo_pago(metodo_pago)
            instance.metodo_pago = metodo_pago

        if nuevo_estado is not None:
            if instance.estado == 'Pagada':
                raise serializers.ValidationError({'estado': 'La cuota ya está pagada.'})

            if not metodo_pago and instance.metodo_pago is None:
                raise serializers.ValidationError({'metodo_pago': 'Debe indicar el método de pago (QR o Efectivo).'})

            # Registrar fecha de pago automáticamente
            instance.fecha_pago = date.today()
            instance.estado = 'Pagada'

            # Actualizar el préstamo: restar monto de la cuota + mora
            prestamo = instance.prestamo
            nuevo_restante = prestamo.monto_restante - (instance.monto_cuota + instance.mora_cuota)
            prestamo.monto_restante = max(nuevo_restante, 0)

            # Actualizar estado del préstamo
            if prestamo.monto_restante <= 0:
                prestamo.estado = 'Completado'
            else:
                # Si quedan cuotas vencidas, el préstamo se mantiene en 'Mora', si no, 'En Curso'
                if prestamo.plan_pagos.filter(estado='Vencida').exists():
                    prestamo.estado = 'Mora'
                else:
                    prestamo.estado = 'En Curso'

            prestamo.save(update_fields=['monto_restante', 'estado', 'updated_at'])

        instance.save()
        return instance

