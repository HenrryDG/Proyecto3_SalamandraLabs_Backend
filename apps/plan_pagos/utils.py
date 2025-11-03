from datetime import date
from decimal import Decimal
from typing import Iterable, Optional

from .models import PlanPago


def calcular_mora(monto_cuota: Decimal, interes_mensual: Decimal, dias_atraso: int) -> Decimal:
    """
    Calcula la mora prorrateando el interés mensual por días de atraso.

    Suposición: la mora es proporcional al interés mensual del préstamo.
    Formula: mora = monto_cuota * (interes_mensual / 100) * (dias_atraso / 30)
    """
    if dias_atraso <= 0:
        return Decimal('0.00')
    mora = monto_cuota * (interes_mensual / Decimal('100')) * (Decimal(dias_atraso) / Decimal('30'))
    return mora.quantize(Decimal('0.01'))


def actualizar_cuotas_vencidas(queryset: Optional[Iterable[PlanPago]] = None) -> int:
    """
    Marca como 'Vencida' las cuotas cuyo vencimiento ya pasó y aún no están pagadas.
    También actualiza la mora en base a los días de atraso y el interés del préstamo.

    Devuelve la cantidad de registros actualizados.
    """
    today = date.today()

    if queryset is None:
        queryset = PlanPago.objects.select_related('prestamo').filter(estado='Pendiente', fecha_vencimiento__lt=today)
    else:
        # Asegurar filtros de solo pendientes vencidos en el conjunto recibido
        queryset = [pp for pp in queryset if pp.estado == 'Pendiente' and pp.fecha_vencimiento < today]

    updated = 0
    for plan in queryset:
        dias_atraso = (today - plan.fecha_vencimiento).days
        interes = plan.prestamo.interes  # porcentaje mensual
        plan.mora_cuota = calcular_mora(plan.monto_cuota, interes, dias_atraso)
        plan.estado = 'Vencida'
        plan.save(update_fields=['mora_cuota', 'estado', 'updated_at'])
        updated += 1

    return updated
