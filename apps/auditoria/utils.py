from apps.auditoria.models import Auditoria
from apps.empleados.models import Empleado

# OBTENER IP DEL CLIENTE DONDE SE REALIZA LA ACCIÓN

def get_client_ip(request):
    """Obtiene la IP del cliente desde el request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip



####################################################################
######## FUNCIONES DE REGISTRO DE LOGIN EN LA AUDITORÍA ############
####################################################################

def registrar_login(request, user, empleado=None):
    """Crea un registro de auditoría para login."""
    if empleado is None:
        try:
            empleado = Empleado.objects.get(user=user)
        except Empleado.DoesNotExist:
            empleado = None

    nombre = f"{empleado.nombre} {empleado.apellido_paterno or ''} {empleado.apellido_materno or ''}" if empleado else ""
    descripcion = f"El usuario {user.username} ({nombre}) inició sesión vía API"
    
    Auditoria.objects.create(
        usuario=user,
        accion='LOGIN',
        tabla='auth_user',
        descripcion=descripcion,
        ip=get_client_ip(request)
    )

def registrar_logout(request, user, empleado=None):
    """Crea un registro de auditoría para logout."""
    if empleado is None:
        try:
            empleado = Empleado.objects.get(user=user)
        except Empleado.DoesNotExist:
            empleado = None

    nombre = f"{empleado.nombre} {empleado.apellido_paterno or ''} {empleado.apellido_materno or ''}" if empleado else ""
    descripcion = f"El usuario {user.username} ({nombre}) cerró sesión vía API"
    
    Auditoria.objects.create(
        usuario=user,
        accion='LOGOUT',
        tabla='auth_user',
        descripcion=descripcion,
        ip=get_client_ip(request)
    )