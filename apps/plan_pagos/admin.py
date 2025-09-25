from django.contrib import admin
from .models import PlanPago

@admin.register(PlanPago)
class PlanPagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'prestamo', 'fecha_pago', 'fecha_vencimiento', 'monto_cuota', 'estado')
    list_filter = ('estado', 'fecha_vencimiento')
