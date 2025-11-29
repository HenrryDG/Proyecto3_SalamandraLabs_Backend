from django.urls import path
from . import views

urlpatterns = [
    # Rutas RESTful
    path('prestamos/', views.prestamo_collection, name='prestamo-collection'),  # GET (listar) y POST (crear)
    path('cliente/<int:cliente_id>/prestamos/', views.prestamos_por_cliente, name='prestamos-por-cliente'),
]