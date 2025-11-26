from django.urls import path
from .views import (
    DashboardResumenView,
)

urlpatterns = [
    # Resumen general
    path('dashboard/resumen/', DashboardResumenView.as_view(), name='dashboard-resumen'),
]
