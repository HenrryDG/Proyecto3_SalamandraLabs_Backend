from django.contrib import admin
from .models import Auditoria

@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'usuario', 'accion', 'tabla')
    list_filter = ('accion', 'tabla', 'usuario')
    search_fields = ('descripcion',)
