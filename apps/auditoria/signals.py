from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from .models import Auditoria

# --------------------
# LOGIN
# --------------------
@receiver(user_logged_in)
def registrar_login(sender, request, user, **kwargs):
    Auditoria.objects.create(
        usuario=user,
        accion='LOGIN',
        tabla='auth_user',
        descripcion=f'El usuario {user.username} inició sesión.',
        ip=request.META.get('REMOTE_ADDR')  # IP del usuario
    )

# --------------------
# LOGOUT
# --------------------
@receiver(user_logged_out)
def registrar_logout(sender, request, user, **kwargs):
    Auditoria.objects.create(
        usuario=user,
        accion='LOGOUT',
        tabla='auth_user',
        descripcion=f'El usuario {user.username} cerró sesión.',
        ip=request.META.get('REMOTE_ADDR')  # IP del usuario
    )
