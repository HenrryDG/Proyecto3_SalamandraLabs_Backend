from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Empleado
from .serializers import EmpleadoSerializer
from drf_spectacular.utils import extend_schema
from django.contrib.auth.models import User


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
@extend_schema(
    methods=["POST"],
    request=EmpleadoSerializer,
    responses={201: EmpleadoSerializer},
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def empleado_collection(request):
    #GET - Listar todos los empleados
    if request.method == 'GET':
        try:
            empleados = Empleado.objects.all()          
            serializer = EmpleadoSerializer(empleados, many=True)
            return Response(serializer.data, status=200)
        except Exception as e:
            return Response({
                'mensaje': 'Error al recuperar los empleados',
                'error': str(e)
            }, status=500)
            
            # POST - Crear un nuevo empleado
    elif request.method == 'POST':
        serializer = EmpleadoSerializer(data=request.data)
        if serializer.is_valid():
            try:
                empleado = serializer.save()
                return Response(serializer.data, status=201)
            except Exception as e:
                return Response({
                    'mensaje': 'Error al crear el empleado',
                    'error': str(e)
                }, status=500)
        return Response({
            'mensaje': 'Error en los datos proporcionados',
            'errores': serializer.errors
        }, status=400)
    
