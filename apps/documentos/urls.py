from django.urls import path
from . import views

urlpatterns = [
    path('documentos/', views.documento_collection, name='documento-collection'),  # GET (listar)
    path('documentos/verificar-carnet/', views.verificar_carnet, name='verificar-carnet'),  # POST (verificar carnet)
    path('documentos/verificar-direccion/', views.verificar_direccion, name='verificar-direccion'),  # POST (verificar dirección)
]