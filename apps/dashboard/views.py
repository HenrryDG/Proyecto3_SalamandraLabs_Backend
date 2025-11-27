from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Avg, Q, F
from django.db.models.functions import ExtractYear, ExtractMonth, Coalesce
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
from collections import defaultdict

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

class SolicitudesEstadisticasView(APIView):
    """
    GET - Estadísticas detalladas de solicitudes de préstamo.
    /api/dashboard/solicitudes/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Distribución por estado
        distribucion_estado = SolicitudPrestamo.objects.values('estado').annotate(
            cantidad=Count('id'),
            monto_total=Coalesce(Sum('monto_solicitado'), Decimal('0'))
        ).order_by('estado')

        # Monto promedio solicitado
        monto_promedio = SolicitudPrestamo.objects.aggregate(
            promedio=Coalesce(Avg('monto_solicitado'), Decimal('0'))
        )['promedio']

        # Solicitudes recientes (últimas 7 días)
        siete_dias_atras = timezone.now() - timedelta(days=7)
        solicitudes_recientes = SolicitudPrestamo.objects.filter(
            created_at__gte=siete_dias_atras
        ).count()

        data = {
            'total': SolicitudPrestamo.objects.count(),
            'monto_promedio': float(monto_promedio),
            'solicitudes_recientes_7_dias': solicitudes_recientes,
            'distribucion_estado': list(distribucion_estado),
        }

        return Response(data, status=status.HTTP_200_OK)

class PrestamosEstadisticasView(APIView):
    """
    GET - Estadísticas detalladas de préstamos
    /api/dashboard/prestamos/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Distribución por estado
        distribucion_estado = Prestamo.objects.values('estado').annotate(
            cantidad=Count('id'),
            monto_total=Coalesce(Sum('monto_aprobado'), Decimal('0')),
            monto_restante=Coalesce(Sum('monto_restante'), Decimal('0'))
        ).order_by('estado')

        # Distribución por plazo
        distribucion_plazo = Prestamo.objects.exclude(
            plazo_meses__isnull=True
        ).values('plazo_meses').annotate(
            cantidad=Count('id')
        ).order_by('plazo_meses')

        # Tasa de interés promedio
        interes_promedio = Prestamo.objects.aggregate(
            promedio=Coalesce(Avg('interes'), Decimal('0'))
        )['promedio']

        # Monto promedio aprobado
        monto_promedio = Prestamo.objects.aggregate(
            promedio=Coalesce(Avg('monto_aprobado'), Decimal('0'))
        )['promedio']

        # Resumen financiero
        resumen_financiero = {
            'total_desembolsado': float(Prestamo.objects.aggregate(
                total=Coalesce(Sum('monto_aprobado'), Decimal('0'))
            )['total']),
            'total_por_cobrar': float(Prestamo.objects.filter(
                estado__in=['En Curso', 'Mora']
            ).aggregate(total=Coalesce(Sum('monto_restante'), Decimal('0')))['total']),
            'total_cobrado': float(Prestamo.objects.aggregate(
                total=Coalesce(Sum(F('monto_aprobado') - F('monto_restante')), Decimal('0'))
            )['total']),
        }

        data = {
            'total': Prestamo.objects.count(),
            'interes_promedio': float(interes_promedio),
            'monto_promedio': float(monto_promedio),
            'distribucion_estado': list(distribucion_estado),
            'distribucion_plazo': list(distribucion_plazo),
            'resumen_financiero': resumen_financiero,
        }
        
        return Response(data, status=status.HTTP_200_OK)

class PlanPagosEstadisticasView(APIView):
    """
    GET - Estadísticas detalladas del plan de pagos
    /api/dashboard/plan-pagos/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Distribución por estado
        distribucion_estado = PlanPago.objects.values('estado').annotate(
            cantidad=Count('id'),
            monto_total=Coalesce(Sum('monto_cuota'), Decimal('0')),
            mora_total=Coalesce(Sum('mora_cuota'), Decimal('0'))
        ).order_by('estado')

        # Pagos por método
        distribucion_metodo = PlanPago.objects.exclude(
            metodo_pago__isnull=True
        ).values('metodo_pago').annotate(
            cantidad=Count('id'),
            monto_total=Coalesce(Sum('monto_cuota'), Decimal('0'))
        ).order_by('-cantidad')

        # Cuotas por vencer (próximos 30 días)
        hoy = timezone.now().date()
        en_30_dias = hoy + timedelta(days=30)
        cuotas_por_vencer = PlanPago.objects.filter(
            estado='Pendiente',
            fecha_vencimiento__gte=hoy,
            fecha_vencimiento__lte=en_30_dias
        ).aggregate(
            cantidad=Count('id'),
            monto_total=Coalesce(Sum('monto_cuota'), Decimal('0'))
        )

        # Cuotas vencidas (ya pasaron la fecha de vencimiento)
        cuotas_vencidas = PlanPago.objects.filter(
            estado='Vencida'
        ).aggregate(
            cantidad=Count('id'),
            monto_total=Coalesce(Sum('monto_cuota'), Decimal('0')),
            mora_total=Coalesce(Sum('mora_cuota'), Decimal('0'))
        )

        # Resumen de recaudación
        resumen_recaudacion = {
            'total_recaudado': float(PlanPago.objects.filter(estado='Pagada').aggregate(
                total=Coalesce(Sum('monto_cuota'), Decimal('0'))
            )['total']),
            'mora_recaudada': float(PlanPago.objects.filter(estado='Pagada').aggregate(
                total=Coalesce(Sum('mora_cuota'), Decimal('0'))
            )['total']),
            'pendiente_por_cobrar': float(PlanPago.objects.filter(
                estado__in=['Pendiente', 'Vencida']
            ).aggregate(total=Coalesce(Sum('monto_cuota'), Decimal('0')))['total']),
        }

        data = {
            'total_cuotas': PlanPago.objects.count(),
            'distribucion_estado': list(distribucion_estado),
            'distribucion_metodo_pago': list(distribucion_metodo),
            'cuotas_por_vencer_30_dias': cuotas_por_vencer,
            'cuotas_vencidas': cuotas_vencidas,
            'resumen_recaudacion': resumen_recaudacion,
        }
        
        return Response(data, status=status.HTTP_200_OK)
