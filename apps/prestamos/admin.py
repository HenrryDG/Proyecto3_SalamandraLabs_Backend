from django.contrib import admin
from .models import Prestamo

@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'empleado', 'monto', 'interes', 'fecha_solicitud', 'estado_aprobacion')
    list_filter = ('estado_aprobacion', 'fecha_solicitud')
    search_fields = ('cliente__nombre', 'empleado__nombre')
