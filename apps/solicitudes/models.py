from django.db import models
from apps.empleados.models import Empleado
from apps.clientes.models import Cliente


class SolicitudPrestamo(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.PROTECT, related_name='solicitudes')
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='solicitudes')

    monto_solicitado = models.DecimalField(max_digits=12, decimal_places=2)
    proposito = models.TextField()
    plazo_meses = models.IntegerField()
    fecha_solicitud = models.DateField(auto_now_add=True)
    fecha_aprobacion = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=[
        ('Pendiente', 'Pendiente'), 
        ('Aprobada', 'Aprobada'), 
        ('Rechazada', 'Rechazada')
    ], default='Pendiente')
    observaciones = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'solicitudes_prestamos'
    
    def __str__(self):
        return f"Solicitud {self.id} - {self.cliente.nombre} {self.cliente.apellido_paterno}"



