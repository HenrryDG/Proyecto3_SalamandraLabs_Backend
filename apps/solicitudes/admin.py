from django.contrib import admin
from .models import SolicitudPrestamo

@admin.register(SolicitudPrestamo)
class SolicitudPrestamoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'empleado', 'monto_solicitado', 'plazo_meses', 'estado', 'fecha_solicitud')
    list_filter = ('estado', 'fecha_solicitud')
    search_fields = ('cliente__nombre', 'cliente__apellido_paterno', 'empleado__nombre', 'empleado__apellido_paterno')

    # Métodos para mostrar datos relacionados
    def cliente(self, obj):
        return f"{obj.cliente.nombre} {obj.cliente.apellido_paterno}"
    cliente.short_description = 'Cliente'

    def empleado(self, obj):
        return f"{obj.empleado.nombre} {obj.empleado.apellido_paterno}"
    empleado.short_description = 'Empleado'
