from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Cliente
from .serializers import ClienteSerializer
from drf_spectacular.utils import extend_schema


@extend_schema(
    methods=["POST"],
    request=ClienteSerializer,
    responses={201: ClienteSerializer},
)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def cliente_collection(request):
    # Listar todos los clientes
    if request.method == 'GET':
        try:
            clientes = Cliente.objects.all()          
            serializer = ClienteSerializer(clientes, many=True)
            return Response(serializer.data, status=200)

        except Exception as e:
            return Response({
                'mensaje': 'Error al recuperar los clientes',
                'error': str(e)
            }, status=500)
    
    # Crear un nuevo cliente
    elif request.method == 'POST':
        serializer = ClienteSerializer(data=request.data)
        if serializer.is_valid():
            try:
                cliente = serializer.save()
                return Response(serializer.data, status=201)
            except Exception as e:
                return Response({
                    'mensaje': 'Error al crear el cliente',
                    'error': str(e)
                }, status=500)
        return Response({
            'mensaje': 'Error en los datos proporcionados',
            'errores': serializer.errors
        }, status=400)


@extend_schema(
    methods=["PUT"],
    request=ClienteSerializer,
    responses={200: ClienteSerializer},
)
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def cliente_element(request, pk):
    try:
        cliente = Cliente.objects.get(pk=pk)
    except Cliente.DoesNotExist:
        return Response({
            'mensaje': 'Cliente no encontrado',
            'error': 'El cliente con el ID proporcionado no existe'
        }, status=404)
    
    # Obtener un cliente específico
    if request.method == 'GET':
        try:
            serializer = ClienteSerializer(cliente)
            return Response(serializer.data, status=200)
        except Exception as e:
            return Response({
                'mensaje': 'Error al procesar los datos del cliente',
                'detalles': str(e)
            }, status=500)
    
    # Actualizar un cliente existente
    elif request.method == 'PUT':
        serializer = ClienteSerializer(cliente, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=200)
            except Exception as e:
                return Response({
                    'mensaje': 'Error al guardar los cambios del cliente',
                    'detalles': str(e)
                }, status=500)
        return Response({
            'mensaje': 'Error en los datos proporcionados para actualizar',
            'errores': serializer.errors
        }, status=400)
    
    # Realizar soft delete del cliente
    elif request.method == 'DELETE':
        try:
            cliente.delete()
            return Response({
                'mensaje': 'Cliente eliminado exitosamente',
                'cliente_id': pk
            }, status=200)
        except Exception as e:
            return Response({
                'mensaje': 'Error al eliminar el cliente',
                'detalles': str(e)
            }, status=500)
