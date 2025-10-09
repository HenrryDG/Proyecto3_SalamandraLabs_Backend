from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [

    # AUTENTICACION JWT
    path('login/', TokenObtainPairView.as_view(), name='api-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # Rutas RESTful
    path('empleados/perfil/', views.empleado_profile, name='empleado-profile'),
    path('empleados/', views.empleado_collection, name='empleado-collection'),
      path('empleados/<int:pk>/', views.empleado_element, name='empleado-element'),
]