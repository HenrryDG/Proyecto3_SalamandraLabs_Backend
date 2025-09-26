from django.contrib import admin
from .models import Prestamo

@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'empleado', 'monto_aprobado', 'monto_restante', 'fecha_desembolso', 'estado')
    list_filter = ('estado',)
    search_fields = ('solicitud__cliente__nombre', 'solicitud__cliente__apellido_paterno', 'solicitud__empleado__nombre')

    # Métodos para mostrar datos relacionados
    def cliente(self, obj):
        return f"{obj.solicitud.cliente.nombre} {obj.solicitud.cliente.apellido_paterno}"
    cliente.short_description = 'Cliente'

    def empleado(self, obj):
        return f"{obj.solicitud.empleado.nombre} {obj.solicitud.empleado.apellido_paterno}"
    empleado.short_description = 'Empleado'
