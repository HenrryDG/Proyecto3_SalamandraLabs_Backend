from django.db import models
from django.contrib.auth.models import User

class Auditoria(models.Model):
    ACCIONES = (
        ('REGISTRO', 'Registro'),
        ('ACTUALIZACIÓN', 'Actualización'),
        ('ELIMINACIÓN', 'Eliminación'),
        ('INICIO DE SESIÓN', 'Inicio de sesión'),
        ('CIERRE DE SESIÓN', 'Cierre de sesión'),
    )

    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=20, choices=ACCIONES)
    tabla = models.CharField(max_length=50)
    descripcion = models.TextField()
    ip = models.GenericIPAddressField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "auditoria"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.fecha} - {self.usuario} - {self.accion} - {self.tabla}"
