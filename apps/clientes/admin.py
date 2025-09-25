from django.contrib import admin
from .models import Cliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'carnet', 'nombre', 'apellido_paterno', 'apellido_materno', 'lugar_trabajo', 'tipo_trabajo', 'ingreso_mensual', 'correo', 'telefono')
    search_fields = ('nombre', 'apellido_paterno', 'apellido_materno', 'carnet')
