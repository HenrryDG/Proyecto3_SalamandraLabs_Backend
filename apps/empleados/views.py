from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Empleado
from .serializers import EmpleadoSerializer
from drf_spectacular.utils import extend_schema


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def empleado_profile(request):
    try:
        # Obtener el empleado asociado al usuario autenticado
        empleado = Empleado.objects.get(user=request.user)
        empleado_data = EmpleadoSerializer(empleado).data
        return Response(empleado_data, status=200)
    except Empleado.DoesNotExist:
        return Response({
            'mensaje': 'Empleado no encontrado para el usuario autenticado'
        }, status=404)
    except Exception as e:
        return Response({
            'mensaje': 'Error al recuperar el perfil del empleado',
            'error': str(e)
        }, status=500)
    
