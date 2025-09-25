from django.db import models
from apps.empleados.models import Empleado
from apps.clientes.models import Cliente

class Prestamo(models.Model):
    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE,
        related_name='prestamos'
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='prestamos'
    )

    monto = models.DecimalField(max_digits=12, decimal_places=2)
    monto_restante = models.DecimalField(max_digits=12, decimal_places=2)
    descripcion = models.CharField(max_length=255)
    interes = models.DecimalField(max_digits=5, decimal_places=2)

    fecha_solicitud = models.DateField()
    fecha_aprobacion = models.DateField(null=True, blank=True)
    estado_aprobacion = models.BooleanField(default=False)  # 0/1 en MySQL → False/True

    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    frecuencia_pagos = models.IntegerField()
    estado_pagos = models.CharField(max_length=20, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'prestamos'

    def __str__(self):
        return f"Préstamo {self.id} - {self.cliente.nombre} {self.cliente.apellido_paterno}"