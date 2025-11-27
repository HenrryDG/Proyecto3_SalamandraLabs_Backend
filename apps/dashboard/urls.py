from django.urls import path
from .views import (
    DashboardResumenView,
    SolicitudesEstadisticasView,
)

urlpatterns = [
    # Resumen general
    path('dashboard/resumen/', DashboardResumenView.as_view(), name='dashboard-resumen'),
    path('dashboard/solicitudes/', SolicitudesEstadisticasView.as_view(), name='dashboard-solicitudes'),
]
