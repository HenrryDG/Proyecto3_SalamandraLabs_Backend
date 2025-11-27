from django.urls import path
from .views import (
    DashboardResumenView,
    SolicitudesEstadisticasView,
    PrestamosEstadisticasView,
    PlanPagosEstadisticasView,
)

urlpatterns = [
    # Resumen general
    path('dashboard/resumen/', DashboardResumenView.as_view(), name='dashboard-resumen'),
    path('dashboard/solicitudes/', SolicitudesEstadisticasView.as_view(), name='dashboard-solicitudes'),
    path('dashboard/prestamos/', PrestamosEstadisticasView.as_view(), name='dashboard-prestamos'),
    path('dashboard/plan-pagos/', PlanPagosEstadisticasView.as_view(), name='dashboard-plan-pagos'),
]
