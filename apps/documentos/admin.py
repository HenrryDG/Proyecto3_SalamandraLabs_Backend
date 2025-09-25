from django.contrib import admin
from .models import Documento

@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ('id', 'prestamo', 'tipo_documento', 'verificado')
    list_filter = ('verificado', 'tipo_documento')
    search_fields = ('tipo_documento',)
