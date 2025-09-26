from django.db import models
from apps.solicitudes.models import SolicitudPrestamo

class Prestamo(models.Model):
    solicitud = models.OneToOneField(SolicitudPrestamo, on_delete=models.PROTECT, related_name='prestamo')
    monto_aprobado = models.DecimalField(max_digits=12, decimal_places=2)
    monto_restante = models.DecimalField(max_digits=12, decimal_places=2)
    interes = models.DecimalField(max_digits=5, decimal_places=2)
    fecha_desembolso = models.DateField(null=True, blank=True)
    fecha_plazo = models.DateField(null=True, blank=True) 
    frecuencia_pagos = models.IntegerField()
    estado = models.CharField(max_length=20, choices=[
        ('En Curso', 'En Curso'), 
        ('Mora', 'Mora'), 
        ('Completado', 'Completado')
    ], default='En Curso')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'prestamos'

    def __str__(self):
        return f"Préstamo {self.id} - {self.solicitud.cliente.nombre} {self.solicitud.cliente.apellido_paterno}"