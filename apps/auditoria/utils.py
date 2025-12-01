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

###################################################################
######### AUDITORIA DE REGISTRO DE CLIENTES #######################
###################################################################

def registrar_creacion_cliente(request, user, cliente):
    """Crea un registro de auditoría para la creación de un cliente."""
    descripcion = f"El usuario {user.username} registró el cliente {cliente.nombre} {cliente.apellido_paterno or ''} {cliente.apellido_materno or ''}."
    
    Auditoria.objects.create(
        usuario=user,
        accion='CREAR',
        tabla='clientes',
        descripcion=descripcion,
        ip=get_client_ip(request)
    )

def registrar_actualizacion_cliente(request, user, cliente, datos_viejos, datos_nuevos):
    """Crea un registro de auditoría para la actualización de un cliente, campo por campo."""
    # Iterar sobre los datos nuevos para comparar con los viejos
    for campo, valor_nuevo in datos_nuevos.items():
        # Obtener el valor viejo para comparación
        valor_viejo = datos_viejos.get(campo)

        # Si el valor ha cambiado, registrar la auditoría
        if valor_viejo != valor_nuevo:
            descripcion = (
                f"El usuario {user.username} actualizó el {campo} del cliente "
                f"{cliente.nombre} {cliente.apellido_paterno or ''} {cliente.apellido_materno or ''} "
                f"de '{valor_viejo}' a '{valor_nuevo}'."
            )

            Auditoria.objects.create(
                usuario=user,
                accion='ACTUALIZAR',
                tabla='clientes',
                descripcion=descripcion,
                ip=get_client_ip(request)
            )


def registrar_estado_cliente(request, user, cliente):
    """Crea un registro de auditoría para el cambio de estado de un cliente."""
    estado = "habilitó" if cliente.activo else "deshabilitó"
    descripcion = f"El usuario {user.username} {estado} al cliente {cliente.nombre} {cliente.apellido_paterno or ''} {cliente.apellido_materno or ''}."
    
    Auditoria.objects.create(
        usuario=user,
        accion='ACTUALIZAR',
        tabla='clientes',
        descripcion=descripcion,
        ip=get_client_ip(request)
    )
    