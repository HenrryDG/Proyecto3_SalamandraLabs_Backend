from django.contrib import admin
from .models import Cliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'carnet', 'nombre', 'apellido_paterno', 'apellido_materno', 'user_username', 'lugar_trabajo', 'tipo_trabajo', 'ingreso_mensual', 'correo', 'telefono', 'activo')
    search_fields = ('nombre', 'apellido_paterno', 'apellido_materno', 'user__username', 'carnet')

    def user_username(self, obj):
        return obj.user.username if obj.user else '(sin usuario)'
    user_username.short_description = 'Username'
