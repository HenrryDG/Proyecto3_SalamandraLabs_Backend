from django.db import models
from apps.solicitudes.models import SolicitudPrestamo

class Documento(models.Model):
    solicitud = models.ForeignKey(SolicitudPrestamo, on_delete=models.PROTECT, related_name='documentos')
    tipo_documento = models.CharField(max_length=30)
    archivo = models.JSONField(null=True, blank=True)
    verificado = models.BooleanField(default=False)   

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'documentos'

    def __str__(self):
        return f"{self.tipo_documento} - Solicitud {self.solicitud.id}"
