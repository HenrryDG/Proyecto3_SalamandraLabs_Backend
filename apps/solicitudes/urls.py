from django.urls import path
from . import views

urlpatterns = [
    # Rutas RESTful
    path('solicitudes/', views.solicitud_collection, name='solicitud-collection'),  # GET (listar) y POST (crear)
    path('solicitudes/<int:pk>/', views.solicitud_element, name='solicitud-element'),  # GET (detalle), PUT/PATCH (actualizar)
    path('solicitudes/verificar-carnet/', views.verificar_carnet, name='verificar-carnet'),  # POST (verificar carnet)
    path('solicitudes/verificar-direccion/', views.verificar_direccion, name='verificar-direccion'),  # POST (verificar dirección)
]