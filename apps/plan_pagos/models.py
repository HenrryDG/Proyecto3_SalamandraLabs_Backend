from django.db import models
from apps.prestamos.models import Prestamo

class PlanPago(models.Model):
    prestamo = models.ForeignKey(
        Prestamo,
        on_delete=models.PROTECT,
        related_name='plan_pagos'
    )
    fecha_pago = models.DateField()
    fecha_vencimiento = models.DateField()
    metodo_pago = models.CharField(max_length=45)
    monto_cuota = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=30)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'plan_pagos'

    def __str__(self):
        return f"Pago {self.id} - Prestamo {self.prestamo.id} - {self.estado}"
