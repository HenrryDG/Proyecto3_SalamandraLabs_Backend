from django.urls import path
from . import views

urlpatterns = [
    # Rutas RESTful 
    path('clientes/', views.cliente_collection, name='cliente-collection'),  # GET (listar) y POST (crear)
    path('clientes/<int:pk>/', views.cliente_element, name='cliente-element'),  # GET (obtener), PUT (actualizar) y DELETE (eliminar)
]