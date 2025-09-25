from django.contrib import admin
from .models import Empleado

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'apellido_paterno', 'apellido_materno', 'user_username', 'correo', 'telefono', 'activo')
    search_fields = ('nombre', 'apellido_paterno', 'apellido_materno', 'correo', 'user__username')

    def user_username(self, obj):
        return obj.user.username if obj.user else '(sin usuario)'
    user_username.short_description = 'Username'
