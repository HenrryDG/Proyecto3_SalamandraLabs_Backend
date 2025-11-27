from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Avg, Q, F
from django.db.models.functions import ExtractYear, ExtractMonth, ExtractDay, ExtractWeek, Coalesce
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

class TendenciasView(APIView):
    """
    GET - Tendencias generales del sistema para gráficos de línea.
    /api/dashboard/tendencias/
    Query params: periodo (7d, 30d, 90d, 365d)
    """
    permission_classes = [IsAuthenticated]

    def _agrupar_por_periodo(self, queryset, fecha_campo, dias):
        """Agrupa los datos según el periodo usando Extract en lugar de Trunc para evitar problemas de timezone"""
        if dias <= 7:
            # Agrupar por día
            return queryset.annotate(
                anio=ExtractYear(fecha_campo),
                mes=ExtractMonth(fecha_campo),
                dia=ExtractDay(fecha_campo)
            ).values('anio', 'mes', 'dia')
        elif dias <= 90:
            # Agrupar por semana
            return queryset.annotate(
                anio=ExtractYear(fecha_campo),
                semana=ExtractWeek(fecha_campo)
            ).values('anio', 'semana')
        else:
            # Agrupar por mes
            return queryset.annotate(
                anio=ExtractYear(fecha_campo),
                mes=ExtractMonth(fecha_campo)
            ).values('anio', 'mes')

    def _formatear_periodo(self, item, dias):
        """Formatea el periodo según la granularidad"""
        if dias <= 7:
            return f"{item['anio']}-{str(item['mes']).zfill(2)}-{str(item['dia']).zfill(2)}"
        elif dias <= 90:
            return f"{item['anio']}-W{str(item['semana']).zfill(2)}"
        else:
            return f"{item['anio']}-{str(item['mes']).zfill(2)}"

    def get(self, request):
        periodo = request.query_params.get('periodo', '30d')
        
        # Calcular fecha de inicio según el periodo
        dias = {'7d': 7, '30d': 30, '90d': 90, '365d': 365}.get(periodo, 30)
        fecha_inicio = timezone.now() - timedelta(days=dias)

        # Tendencia de clientes nuevos
        clientes_qs = Cliente.objects.filter(created_at__gte=fecha_inicio)
        clientes_agrupados = self._agrupar_por_periodo(clientes_qs, 'created_at', dias)
        tendencia_clientes_raw = clientes_agrupados.annotate(cantidad=Count('id')).order_by('anio')
        
        tendencia_clientes = [
            {'periodo': self._formatear_periodo(item, dias), 'cantidad': item['cantidad']}
            for item in tendencia_clientes_raw
        ]

        # Tendencia de solicitudes
        solicitudes_qs = SolicitudPrestamo.objects.filter(created_at__gte=fecha_inicio)
        solicitudes_agrupadas = self._agrupar_por_periodo(solicitudes_qs, 'created_at', dias)
        tendencia_solicitudes_raw = solicitudes_agrupadas.annotate(
            total=Count('id'),
            aprobadas=Count('id', filter=Q(estado='Aprobada')),
            rechazadas=Count('id', filter=Q(estado='Rechazada')),
            pendientes=Count('id', filter=Q(estado='Pendiente'))
        ).order_by('anio')
        
        tendencia_solicitudes = [
            {
                'periodo': self._formatear_periodo(item, dias),
                'total': item['total'],
                'aprobadas': item['aprobadas'],
                'rechazadas': item['rechazadas'],
                'pendientes': item['pendientes']
            }
            for item in tendencia_solicitudes_raw
        ]

        # Tendencia de préstamos desembolsados
        prestamos_qs = Prestamo.objects.filter(created_at__gte=fecha_inicio)
        prestamos_agrupados = self._agrupar_por_periodo(prestamos_qs, 'created_at', dias)
        tendencia_prestamos_raw = prestamos_agrupados.annotate(
            cantidad=Count('id'),
            monto_total=Coalesce(Sum('monto_aprobado'), Decimal('0'))
        ).order_by('anio')
        
        tendencia_prestamos = [
            {
                'periodo': self._formatear_periodo(item, dias),
                'cantidad': item['cantidad'],
                'monto_total': float(item['monto_total'])
            }
            for item in tendencia_prestamos_raw
        ]

        # Tendencia de pagos recibidos
        pagos_qs = PlanPago.objects.filter(
            estado='Pagada',
            fecha_pago__isnull=False,
            fecha_pago__gte=fecha_inicio.date()
        )
        pagos_agrupados = self._agrupar_por_periodo(pagos_qs, 'fecha_pago', dias)
        tendencia_pagos_raw = pagos_agrupados.annotate(
            cantidad=Count('id'),
            monto_total=Coalesce(Sum('monto_cuota'), Decimal('0'))
        ).order_by('anio')
        
        tendencia_pagos = [
            {
                'periodo': self._formatear_periodo(item, dias),
                'cantidad': item['cantidad'],
                'monto_total': float(item['monto_total'])
            }
            for item in tendencia_pagos_raw
        ]

        data = {
            'periodo_seleccionado': periodo,
            'fecha_inicio': fecha_inicio.isoformat(),
            'tendencia_clientes': tendencia_clientes,
            'tendencia_solicitudes': tendencia_solicitudes,
            'tendencia_prestamos': tendencia_prestamos,
            'tendencia_pagos': tendencia_pagos,
        }
        
        return Response(data, status=status.HTTP_200_OK)