from django.urls import path
from . import views

urlpatterns = [
    path('documentos/<int:solicitud_id>/', views.documento_collection, name='documento-collection'),
    path('documentos/verificar-carnet/', views.verificar_carnet, name='verificar-carnet'),  # POST (verificar carnet)
    path('documentos/verificar-direccion/', views.verificar_direccion, name='verificar-direccion'),  # POST (verificar dirección)
    path('documentos/verificar-ingreso/', views.verificar_ingreso, name='verificar-ingreso'),  # POST (verificar ingreso)
]