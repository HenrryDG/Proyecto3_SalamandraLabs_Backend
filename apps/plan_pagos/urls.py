from django.urls import path
from .views import listar_plan_pagos_por_prestamo, actualizar_plan_pago

urlpatterns = [
    path('prestamos/<int:prestamo_id>/plan-pagos/', listar_plan_pagos_por_prestamo, name='listar_plan_pagos_por_prestamo'),
    path('plan-pagos/<int:plan_id>/', actualizar_plan_pago, name='actualizar_plan_pago'),
]
