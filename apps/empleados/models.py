from django.db import models
from django.contrib.auth.models import User

class Empleado(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=45)
    apellido_materno = models.CharField(max_length=30)
    correo = models.CharField(max_length=30, null=True, blank=True)
    telefono = models.BigIntegerField()
    rol = models.CharField(max_length=30)
    activo = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'empleados'
    
    def __str__(self):
        return f"{self.nombre} {self.apellido_paterno} {self.rol}"
    



