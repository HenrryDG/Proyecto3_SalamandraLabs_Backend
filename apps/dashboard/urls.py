from django.urls import path
from .views import (
    DashboardResumenView,
    SolicitudesEstadisticasView,
    PrestamosEstadisticasView,
    PlanPagosEstadisticasView,

    TendenciasView,
)

urlpatterns = [
    # Resumen general, solicitudes, préstamos y plan de pagos
    path('dashboard/resumen/', DashboardResumenView.as_view(), name='dashboard-resumen'),
    path('dashboard/solicitudes/', SolicitudesEstadisticasView.as_view(), name='dashboard-solicitudes'),
    path('dashboard/prestamos/', PrestamosEstadisticasView.as_view(), name='dashboard-prestamos'),
    path('dashboard/plan-pagos/', PlanPagosEstadisticasView.as_view(), name='dashboard-plan-pagos'),

    # Tendencias y gráficos de línea
    path('dashboard/tendencias/', TendenciasView.as_view(), name='dashboard-tendencias'),
    
]
