from django.db import models

class Cliente(models.Model):
    carnet = models.CharField(max_length=12, unique=True)
    nombre = models.CharField(max_length=30)
    apellido_paterno = models.CharField(max_length=30)
    apellido_materno = models.CharField(max_length=30)
    lugar_trabajo = models.CharField(max_length=60)
    tipo_trabajo = models.CharField(max_length=30)
    ingreso_mensual = models.DecimalField(max_digits=12, decimal_places=2)
    direccion = models.CharField(max_length=255)
    correo = models.CharField(max_length=50, null=True, blank=True)
    telefono = models.BigIntegerField(unique=True)
    activo = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clientes'

    def __str__(self):
        return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno}"
