from django.contrib import admin
from .models import Documento

@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'tipo_documento', 'verificado', 'created_at')
    list_filter = ('verificado', 'tipo_documento')
    search_fields = ('tipo_documento', 'solicitud__cliente__nombre', 'solicitud__cliente__apellido_paterno')

    def cliente(self, obj):
        return f"{obj.solicitud.cliente.nombre} {obj.solicitud.cliente.apellido_paterno}"
    cliente.short_description = 'Cliente'
