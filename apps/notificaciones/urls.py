from django.urls import path
from . import views

urlpatterns = [
    # Endpoints para clientes autenticados
    path('notificaciones/mis-notificaciones/', views.mis_notificaciones, name='mis-notificaciones'),
    path('notificaciones/mis-alertas/', views.mis_alertas_emergentes, name='mis-alertas'),
    path('notificaciones/mi-historial/', views.mi_historial_notificaciones, name='mi-historial'),
    path('notificaciones/mi-resumen/', views.mi_resumen_notificaciones, name='mi-resumen'),
    
    # Endpoints para empleados/administradores
    path('notificaciones/cliente/<int:cliente_id>/', views.notificaciones_cliente, name='notificaciones-cliente'),
    path('notificaciones/cliente/<int:cliente_id>/resumen/', views.resumen_cliente, name='resumen-cliente'),
    path('notificaciones/dashboard/', views.alertas_dashboard, name='alertas-dashboard'),
    
    # Configuración
    path('notificaciones/configuracion/', views.configuracion_notificaciones, name='config-notificaciones'),
]
