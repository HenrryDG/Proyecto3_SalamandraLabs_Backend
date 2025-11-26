from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Avg, Q, F
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay, Coalesce
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.clientes.models import Cliente
from apps.empleados.models import Empleado
from apps.solicitudes.models import SolicitudPrestamo
from apps.prestamos.models import Prestamo
from apps.plan_pagos.models import PlanPago
from apps.documentos.models import Documento


class DashboardResumenView(APIView):
    """
    GET - RESUMEN general de todas las métricas clave
    /api/dashboard/resumen/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Clientes
        total_clientes = Cliente.objects.count()
        clientes_activos = Cliente.objects.filter(activo=True).count()
        clientes_inactivos = Cliente.objects.filter(activo=False).count()

        # Empleados
        total_empleados = Empleado.objects.count()
        empleados_activos = Empleado.objects.filter(activo=True).count()
        empleados_inactivos = Empleado.objects.filter(activo=False).count()

        # Solicitudes
        total_solicitudes = SolicitudPrestamo.objects.count()
        solicitudes_pendientes = SolicitudPrestamo.objects.filter(estado='Pendiente').count()
        solicitudes_aprobadas = SolicitudPrestamo.objects.filter(estado='Aprobada').count()
        solicitudes_rechazadas = SolicitudPrestamo.objects.filter(estado='Rechazada').count()
        
        # Préstamos
        total_prestamos = Prestamo.objects.count()
        prestamos_en_curso = Prestamo.objects.filter(estado='En Curso').count()
        prestamos_en_mora = Prestamo.objects.filter(estado='Mora').count()
        prestamos_completados = Prestamo.objects.filter(estado='Completado').count()
        monto_desembolsado = Prestamo.objects.aggregate(
            total=Coalesce(Sum('monto_aprobado'), Decimal('0'))
        )['total']
        monto_restante = Prestamo.objects.filter(
            estado__in=['En Curso', 'Mora']
        ).aggregate(total=Coalesce(Sum('monto_restante'), Decimal('0')))['total']

        # Plan de Pagos
        total_cuotas = PlanPago.objects.count()
        cuotas_pagadas = PlanPago.objects.filter(estado='Pagada').count()
        cuotas_pendientes = PlanPago.objects.filter(estado='Pendiente').count()
        cuotas_vencidas = PlanPago.objects.filter(estado='Vencida').count()
        
        total_recaudado = PlanPago.objects.filter(estado='Pagada').aggregate(
            total=Coalesce(Sum('monto_cuota'), Decimal('0'))
        )['total']
        mora_acumulada = PlanPago.objects.aggregate(
            total=Coalesce(Sum('mora_cuota'), Decimal('0'))
        )['total']

        # Calcular tasas
        tasa_aprobacion = (solicitudes_aprobadas / total_solicitudes * 100) if total_solicitudes > 0 else 0
        tasa_mora = (prestamos_en_mora / total_prestamos * 100) if total_prestamos > 0 else 0
        tasa_cumplimiento = (cuotas_pagadas / total_cuotas * 100) if total_cuotas > 0 else 0

        data = {
            'clientes': {
                'total': total_clientes,
                'activos': clientes_activos,
                'inactivos': clientes_inactivos,
            },
            'empleados': {
                'total': total_empleados,
                'activos': empleados_activos,
                'inactivos': empleados_inactivos,
            },
            'solicitudes': {
                'total': total_solicitudes,
                'pendientes': solicitudes_pendientes,
                'aprobadas': solicitudes_aprobadas,
                'rechazadas': solicitudes_rechazadas,
                'tasa_aprobacion': round(tasa_aprobacion, 2),
            },
            'prestamos': {
                'total': total_prestamos,
                'en_curso': prestamos_en_curso,
                'en_mora': prestamos_en_mora,
                'completados': prestamos_completados,
                'monto_desembolsado': float(monto_desembolsado),
                'monto_restante': float(monto_restante),
                'tasa_mora': round(tasa_mora, 2),
            },
            'pagos': {
                'total_cuotas': total_cuotas,
                'cuotas_pagadas': cuotas_pagadas,
                'cuotas_pendientes': cuotas_pendientes,
                'cuotas_vencidas': cuotas_vencidas,
                'total_recaudado': float(total_recaudado),
                'mora_acumulada': float(mora_acumulada),
                'tasa_cumplimiento': round(tasa_cumplimiento, 2),
            }
        }
        return Response(data, status=status.HTTP_200_OK)

