from django.urls import path
from . import views

urlpatterns = [
    # Rutas RESTful
    path('solicitudes/', views.solicitud_collection, name='solicitud-collection'),  # GET (listar) y POST (crear)
    path('solicitudes/<int:pk>/', views.solicitud_element, name='solicitud-element'),  # GET (detalle), DELETE (eliminar), PUT/PATCH (actualizar)
    path('cliente/<int:cliente_id>/solicitudes/', views.solicitudes_por_cliente, name='solicitudes-por-cliente'),
]