"""
Servicios para la generación dinámica de notificaciones.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from django.db.models import Q

from apps.clientes.models import Cliente
from apps.solicitudes.models import SolicitudPrestamo
from apps.prestamos.models import Prestamo
from apps.plan_pagos.models import PlanPago

from .types import (
    Notificacion,
    TipoNotificacion,
    CategoriaNotificacion,
    PrioridadNotificacion,
    EstiloNotificacion,
    ConfiguracionNotificacion,
    CONFIGURACION_POR_TIPO,
)


# Meses en español para formato legible
MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}


def formato_fecha(dt: date) -> str:
    """Formatea una fecha en español (ej: '15 de noviembre')."""
    return f"{dt.day} de {MESES_ES[dt.month]}"


def formato_fecha_completa(dt: date) -> str:
    """Formatea una fecha completa en español (ej: '15 de noviembre de 2025')."""
    return f"{dt.day} de {MESES_ES[dt.month]} de {dt.year}"


def formato_moneda(valor: Decimal) -> str:
    """Formatea un valor monetario (ej: 'Bs 1,500.00')."""
    return f"Bs {valor:,.2f}"


def obtener_numero_cuota(cuota: PlanPago) -> int:
    """Obtiene el número de cuota dentro del préstamo."""
    cuotas_prestamo = list(
        PlanPago.objects.filter(prestamo=cuota.prestamo)
        .order_by("fecha_vencimiento")
        .values_list('id', flat=True)
    )
    try:
        return cuotas_prestamo.index(cuota.id) + 1
    except ValueError:
        return 1


def crear_notificacion(
    tipo: TipoNotificacion,
    titulo: str,
    mensaje: str,
    cliente_id: int,
    id_suffix: str,
    solicitud_id: Optional[int] = None,
    prestamo_id: Optional[int] = None,
    plan_pago_id: Optional[int] = None,
    fecha_evento: Optional[date] = None,
    datos_extra: Optional[dict] = None,
    override_prioridad: Optional[PrioridadNotificacion] = None,
    override_estilo: Optional[EstiloNotificacion] = None,
    override_categoria: Optional[CategoriaNotificacion] = None,
) -> Notificacion:
    """
    Crea una notificación con configuración predeterminada según el tipo.
    """
    config = CONFIGURACION_POR_TIPO.get(tipo, {})
    
    return Notificacion(
        id=f"{tipo.value}_{id_suffix}",
        tipo=tipo,
        categoria=override_categoria or config.get("categoria", CategoriaNotificacion.PERSISTENTE),
        titulo=titulo,
        mensaje=mensaje,
        cliente_id=cliente_id,
        solicitud_id=solicitud_id,
        prestamo_id=prestamo_id,
        plan_pago_id=plan_pago_id,
        prioridad=override_prioridad or config.get("prioridad", PrioridadNotificacion.MEDIA),
        estilo=override_estilo or config.get("estilo", EstiloNotificacion.INFO),
        fecha_evento=fecha_evento,
        datos_extra=datos_extra or {},
    )


class NotificacionService:
    """
    Servicio principal para generar notificaciones basadas en el estado del sistema.
    """
    
    def __init__(self, config: Optional[ConfiguracionNotificacion] = None):
        self.config = config or ConfiguracionNotificacion()
        self.hoy = date.today()
    
    # =========================================================================
    # NOTIFICACIONES DE SOLICITUDES
    # =========================================================================
    
    def generar_notificaciones_solicitud(self, solicitud: SolicitudPrestamo) -> List[Notificacion]:
        """
        Genera notificaciones basadas en el estado de una solicitud.
        """
        notificaciones = []
        cliente = solicitud.cliente
        
        if solicitud.estado == "Pendiente":
            # Solicitud en proceso de revisión
            dias_espera = (self.hoy - solicitud.fecha_solicitud).days
            
            notificaciones.append(crear_notificacion(
                tipo=TipoNotificacion.NUEVA_SOLICITUD,
                titulo="Solicitud en revisión",
                mensaje=f"Tu solicitud de préstamo por {formato_moneda(solicitud.monto_solicitado)} "
                        f"está siendo evaluada. Fecha de solicitud: {formato_fecha_completa(solicitud.fecha_solicitud)}.",
                cliente_id=cliente.id,
                id_suffix=f"solicitud_{solicitud.id}_pendiente",
                solicitud_id=solicitud.id,
                fecha_evento=solicitud.fecha_solicitud,
                datos_extra={
                    "monto_solicitado": str(solicitud.monto_solicitado),
                    "dias_espera": dias_espera,
                    "proposito": solicitud.proposito,
                },
            ))
            
        elif solicitud.estado == "Aprobada":
            # Verificar si ya tiene préstamo asociado
            tiene_prestamo = hasattr(solicitud, 'prestamo') and solicitud.prestamo is not None
            
            if tiene_prestamo:
                notificaciones.append(crear_notificacion(
                    tipo=TipoNotificacion.SOLICITUD_APROBADA,
                    titulo="¡Solicitud aprobada!",
                    mensaje=f"Tu solicitud de préstamo ha sido aprobada. "
                            f"Monto aprobado: {formato_moneda(solicitud.prestamo.monto_aprobado)}. "
                            f"Fecha de aprobación: {formato_fecha_completa(solicitud.fecha_aprobacion)}.",
                    cliente_id=cliente.id,
                    id_suffix=f"solicitud_{solicitud.id}_aprobada",
                    solicitud_id=solicitud.id,
                    prestamo_id=solicitud.prestamo.id,
                    fecha_evento=solicitud.fecha_aprobacion,
                    datos_extra={
                        "monto_solicitado": str(solicitud.monto_solicitado),
                        "monto_aprobado": str(solicitud.prestamo.monto_aprobado),
                    },
                ))
            else:
                notificaciones.append(crear_notificacion(
                    tipo=TipoNotificacion.SOLICITUD_APROBADA,
                    titulo="¡Solicitud aprobada!",
                    mensaje=f"Tu solicitud de préstamo por {formato_moneda(solicitud.monto_solicitado)} "
                            f"ha sido aprobada. Pronto se procesará el desembolso.",
                    cliente_id=cliente.id,
                    id_suffix=f"solicitud_{solicitud.id}_aprobada",
                    solicitud_id=solicitud.id,
                    fecha_evento=solicitud.fecha_aprobacion,
                    datos_extra={
                        "monto_solicitado": str(solicitud.monto_solicitado),
                    },
                ))
                
        elif solicitud.estado == "Rechazada":
            mensaje_rechazo = f"Lamentablemente, tu solicitud de préstamo por {formato_moneda(solicitud.monto_solicitado)} no fue aprobada."
            if solicitud.observaciones:
                mensaje_rechazo += f" Motivo: {solicitud.observaciones}"
            
            notificaciones.append(crear_notificacion(
                tipo=TipoNotificacion.SOLICITUD_RECHAZADA,
                titulo="Solicitud no aprobada",
                mensaje=mensaje_rechazo,
                cliente_id=cliente.id,
                id_suffix=f"solicitud_{solicitud.id}_rechazada",
                solicitud_id=solicitud.id,
                fecha_evento=solicitud.fecha_aprobacion,
                datos_extra={
                    "monto_solicitado": str(solicitud.monto_solicitado),
                    "observaciones": solicitud.observaciones,
                },
            ))
        
        return notificaciones
    
    # =========================================================================
    # NOTIFICACIONES DE PRÉSTAMOS
    # =========================================================================
    
    def generar_notificaciones_prestamo(self, prestamo: Prestamo) -> List[Notificacion]:
        """
        Genera notificaciones basadas en el estado de un préstamo.
        """
        notificaciones = []
        cliente = prestamo.solicitud.cliente
        
        if prestamo.estado == "En Curso":
            # Información del préstamo activo
            cuotas_pagadas = prestamo.plan_pagos.filter(estado="Pagada").count()
            total_cuotas = prestamo.plan_pagos.count()
            
            notificaciones.append(crear_notificacion(
                tipo=TipoNotificacion.PRESTAMO_DESEMBOLSADO,
                titulo="Préstamo activo",
                mensaje=f"Tu préstamo de {formato_moneda(prestamo.monto_aprobado)} está en curso. "
                        f"Progreso: {cuotas_pagadas}/{total_cuotas} cuotas pagadas. "
                        f"Saldo pendiente: {formato_moneda(prestamo.monto_restante)}.",
                cliente_id=cliente.id,
                id_suffix=f"prestamo_{prestamo.id}_activo",
                prestamo_id=prestamo.id,
                solicitud_id=prestamo.solicitud.id,
                datos_extra={
                    "monto_aprobado": str(prestamo.monto_aprobado),
                    "monto_restante": str(prestamo.monto_restante),
                    "cuotas_pagadas": cuotas_pagadas,
                    "total_cuotas": total_cuotas,
                    "progreso_porcentaje": round((cuotas_pagadas / total_cuotas) * 100, 1) if total_cuotas > 0 else 0,
                },
            ))
            
        elif prestamo.estado == "Mora":
            # Préstamo en mora - notificación urgente
            cuotas_vencidas = prestamo.plan_pagos.filter(estado="Vencida")
            total_mora = sum(c.mora_cuota for c in cuotas_vencidas)
            
            notificaciones.append(crear_notificacion(
                tipo=TipoNotificacion.PRESTAMO_EN_MORA,
                titulo="⚠️ Préstamo en mora",
                mensaje=f"Tu préstamo tiene {cuotas_vencidas.count()} cuota(s) vencida(s). "
                        f"Mora acumulada: {formato_moneda(total_mora)}. "
                        f"Por favor, regulariza tus pagos lo antes posible.",
                cliente_id=cliente.id,
                id_suffix=f"prestamo_{prestamo.id}_mora",
                prestamo_id=prestamo.id,
                solicitud_id=prestamo.solicitud.id,
                datos_extra={
                    "cuotas_vencidas": cuotas_vencidas.count(),
                    "total_mora": str(total_mora),
                    "monto_restante": str(prestamo.monto_restante),
                },
            ))
            
        elif prestamo.estado == "Completado":
            notificaciones.append(crear_notificacion(
                tipo=TipoNotificacion.PRESTAMO_COMPLETADO,
                titulo="🎉 ¡Préstamo completado!",
                mensaje=f"¡Felicitaciones! Has completado el pago de tu préstamo de "
                        f"{formato_moneda(prestamo.monto_aprobado)}. "
                        f"Gracias por tu confianza.",
                cliente_id=cliente.id,
                id_suffix=f"prestamo_{prestamo.id}_completado",
                prestamo_id=prestamo.id,
                solicitud_id=prestamo.solicitud.id,
                datos_extra={
                    "monto_aprobado": str(prestamo.monto_aprobado),
                    "fecha_desembolso": prestamo.fecha_desembolso.isoformat() if prestamo.fecha_desembolso else None,
                },
            ))
        
        return notificaciones
    
    # =========================================================================
    # NOTIFICACIONES DE PLAN DE PAGOS (CUOTAS)
    # =========================================================================
    
    def generar_notificaciones_cuota(self, cuota: PlanPago) -> List[Notificacion]:
        """
        Genera notificaciones basadas en el estado de una cuota.
        """
        notificaciones = []
        cliente = cuota.prestamo.solicitud.cliente
        numero_cuota = obtener_numero_cuota(cuota)
        total_cuotas = cuota.prestamo.plan_pagos.count()
        
        dias_para_vencer = (cuota.fecha_vencimiento - self.hoy).days
        
        if cuota.estado == "Pendiente":
            # Cuota pendiente - verificar proximidad al vencimiento
            
            if dias_para_vencer == 0:
                # Vence hoy
                notificaciones.append(crear_notificacion(
                    tipo=TipoNotificacion.CUOTA_VENCE_HOY,
                    titulo="⚠️ Cuota vence hoy",
                    mensaje=f"La cuota N° {numero_cuota} de {total_cuotas} vence HOY. "
                            f"Monto: {formato_moneda(cuota.monto_cuota)}. "
                            f"Realiza tu pago para evitar mora.",
                    cliente_id=cliente.id,
                    id_suffix=f"cuota_{cuota.id}_vence_hoy",
                    plan_pago_id=cuota.id,
                    prestamo_id=cuota.prestamo.id,
                    fecha_evento=cuota.fecha_vencimiento,
                    datos_extra={
                        "numero_cuota": numero_cuota,
                        "total_cuotas": total_cuotas,
                        "monto_cuota": str(cuota.monto_cuota),
                    },
                ))
                
            elif dias_para_vencer == 1:
                # Vence mañana
                notificaciones.append(crear_notificacion(
                    tipo=TipoNotificacion.CUOTA_PROXIMA_VENCER,
                    titulo="Cuota vence mañana",
                    mensaje=f"La cuota N° {numero_cuota} de {total_cuotas} vence mañana, "
                            f"{formato_fecha(cuota.fecha_vencimiento)}. "
                            f"Monto: {formato_moneda(cuota.monto_cuota)}.",
                    cliente_id=cliente.id,
                    id_suffix=f"cuota_{cuota.id}_vence_manana",
                    plan_pago_id=cuota.id,
                    prestamo_id=cuota.prestamo.id,
                    fecha_evento=cuota.fecha_vencimiento,
                    override_prioridad=PrioridadNotificacion.ALTA,
                    datos_extra={
                        "numero_cuota": numero_cuota,
                        "total_cuotas": total_cuotas,
                        "monto_cuota": str(cuota.monto_cuota),
                        "dias_restantes": 1,
                    },
                ))
                
            elif 2 <= dias_para_vencer <= 3:
                # Vence en 2-3 días - urgente
                notificaciones.append(crear_notificacion(
                    tipo=TipoNotificacion.CUOTA_PROXIMA_VENCER,
                    titulo="Cuota próxima a vencer",
                    mensaje=f"La cuota N° {numero_cuota} vence en {dias_para_vencer} días "
                            f"({formato_fecha(cuota.fecha_vencimiento)}). "
                            f"Monto: {formato_moneda(cuota.monto_cuota)}.",
                    cliente_id=cliente.id,
                    id_suffix=f"cuota_{cuota.id}_proxima_{dias_para_vencer}d",
                    plan_pago_id=cuota.id,
                    prestamo_id=cuota.prestamo.id,
                    fecha_evento=cuota.fecha_vencimiento,
                    override_prioridad=PrioridadNotificacion.ALTA,
                    datos_extra={
                        "numero_cuota": numero_cuota,
                        "total_cuotas": total_cuotas,
                        "monto_cuota": str(cuota.monto_cuota),
                        "dias_restantes": dias_para_vencer,
                    },
                ))
                
            elif 4 <= dias_para_vencer <= self.config.dias_anticipacion_recordatorio:
                # Recordatorio estándar (4-7 días)
                notificaciones.append(crear_notificacion(
                    tipo=TipoNotificacion.RECORDATORIO_CUOTA,
                    titulo="Recordatorio de pago",
                    mensaje=f"Tu cuota N° {numero_cuota} vence el {formato_fecha(cuota.fecha_vencimiento)} "
                            f"(en {dias_para_vencer} días). "
                            f"Monto: {formato_moneda(cuota.monto_cuota)}.",
                    cliente_id=cliente.id,
                    id_suffix=f"cuota_{cuota.id}_recordatorio",
                    plan_pago_id=cuota.id,
                    prestamo_id=cuota.prestamo.id,
                    fecha_evento=cuota.fecha_vencimiento,
                    datos_extra={
                        "numero_cuota": numero_cuota,
                        "total_cuotas": total_cuotas,
                        "monto_cuota": str(cuota.monto_cuota),
                        "dias_restantes": dias_para_vencer,
                    },
                ))
                
        elif cuota.estado == "Vencida":
            # Cuota vencida
            dias_mora = (self.hoy - cuota.fecha_vencimiento).days
            monto_total = cuota.monto_cuota + cuota.mora_cuota
            
            mensaje = f"La cuota N° {numero_cuota} está vencida desde el {formato_fecha(cuota.fecha_vencimiento)} "
            mensaje += f"({dias_mora} día(s) de atraso). "
            mensaje += f"Monto original: {formato_moneda(cuota.monto_cuota)}. "
            
            if cuota.mora_cuota > 0:
                mensaje += f"Mora: {formato_moneda(cuota.mora_cuota)}. "
                mensaje += f"Total a pagar: {formato_moneda(monto_total)}."
            
            notificaciones.append(crear_notificacion(
                tipo=TipoNotificacion.CUOTA_VENCIDA,
                titulo="🚨 Cuota vencida",
                mensaje=mensaje,
                cliente_id=cliente.id,
                id_suffix=f"cuota_{cuota.id}_vencida",
                plan_pago_id=cuota.id,
                prestamo_id=cuota.prestamo.id,
                fecha_evento=cuota.fecha_vencimiento,
                datos_extra={
                    "numero_cuota": numero_cuota,
                    "total_cuotas": total_cuotas,
                    "monto_cuota": str(cuota.monto_cuota),
                    "mora_cuota": str(cuota.mora_cuota),
                    "monto_total": str(monto_total),
                    "dias_mora": dias_mora,
                },
            ))
            
        elif cuota.estado == "Pagada":
            # Cuota pagada - notificación de confirmación
            notificaciones.append(crear_notificacion(
                tipo=TipoNotificacion.PAGO_COMPLETADO,
                titulo="✅ Pago registrado",
                mensaje=f"Se registró el pago de la cuota N° {numero_cuota} de {total_cuotas}. "
                        f"Monto pagado: {formato_moneda(cuota.monto_cuota + cuota.mora_cuota)}. "
                        f"Fecha de pago: {formato_fecha_completa(cuota.fecha_pago) if cuota.fecha_pago else 'Registrado'}.",
                cliente_id=cliente.id,
                id_suffix=f"cuota_{cuota.id}_pagada",
                plan_pago_id=cuota.id,
                prestamo_id=cuota.prestamo.id,
                fecha_evento=cuota.fecha_pago,
                datos_extra={
                    "numero_cuota": numero_cuota,
                    "total_cuotas": total_cuotas,
                    "monto_pagado": str(cuota.monto_cuota + cuota.mora_cuota),
                    "metodo_pago": cuota.metodo_pago,
                },
            ))
        
        return notificaciones
    
    # =========================================================================
    # MÉTODOS PRINCIPALES DE OBTENCIÓN DE NOTIFICACIONES
    # =========================================================================
    
    def obtener_notificaciones_cliente(
        self,
        cliente_id: int,
        incluir_emergentes: bool = True,
        incluir_persistentes: bool = True,
        solo_no_leidas: bool = False,
    ) -> List[Notificacion]:
        """
        Obtiene todas las notificaciones para un cliente específico.
        """
        notificaciones = []
        
        try:
            cliente = Cliente.objects.get(pk=cliente_id)
        except Cliente.DoesNotExist:
            return notificaciones
        
        # Obtener solicitudes del cliente
        solicitudes = SolicitudPrestamo.objects.filter(cliente=cliente)
        for solicitud in solicitudes:
            notificaciones.extend(self.generar_notificaciones_solicitud(solicitud))
        
        # Obtener préstamos del cliente
        prestamos = Prestamo.objects.filter(
            solicitud__cliente=cliente
        ).select_related('solicitud')
        
        for prestamo in prestamos:
            notificaciones.extend(self.generar_notificaciones_prestamo(prestamo))
            
            # Obtener cuotas del préstamo
            cuotas = prestamo.plan_pagos.all().order_by('fecha_vencimiento')
            for cuota in cuotas:
                notificaciones.extend(self.generar_notificaciones_cuota(cuota))
        
        # Filtrar por categoría si es necesario
        if not incluir_emergentes:
            notificaciones = [
                n for n in notificaciones 
                if n.categoria != CategoriaNotificacion.EMERGENTE
            ]
        
        if not incluir_persistentes:
            notificaciones = [
                n for n in notificaciones 
                if n.categoria != CategoriaNotificacion.PERSISTENTE
            ]
        
        # Ordenar por prioridad (urgente primero) y fecha
        prioridad_orden = {
            PrioridadNotificacion.URGENTE: 0,
            PrioridadNotificacion.ALTA: 1,
            PrioridadNotificacion.MEDIA: 2,
            PrioridadNotificacion.BAJA: 3,
        }
        
        notificaciones.sort(
            key=lambda n: (prioridad_orden.get(n.prioridad, 2), n.fecha_generacion),
            reverse=False  # Urgentes primero, más recientes después
        )
        
        return notificaciones
    
    def obtener_notificaciones_emergentes(self, cliente_id: int) -> List[Notificacion]:
        """
        Obtiene solo las notificaciones emergentes/alertas para un cliente.
        Estas son las que deben mostrarse como popups o alertas inmediatas.
        """
        todas = self.obtener_notificaciones_cliente(
            cliente_id,
            incluir_emergentes=True,
            incluir_persistentes=False,
        )
        
        # Filtrar solo emergentes y ambas
        return [
            n for n in todas 
            if n.categoria in [CategoriaNotificacion.EMERGENTE, CategoriaNotificacion.AMBAS]
        ]
    
    def obtener_historial_notificaciones(self, cliente_id: int) -> List[Notificacion]:
        """
        Obtiene el historial de notificaciones persistentes para un cliente.
        Estas aparecen en la lista/bandeja de notificaciones de la app.
        """
        todas = self.obtener_notificaciones_cliente(
            cliente_id,
            incluir_emergentes=False,
            incluir_persistentes=True,
        )
        
        # Incluir persistentes y ambas
        return [
            n for n in todas 
            if n.categoria in [CategoriaNotificacion.PERSISTENTE, CategoriaNotificacion.AMBAS]
        ]
    
    def obtener_resumen_notificaciones(self, cliente_id: int) -> Dict[str, Any]:
        """
        Obtiene un resumen de notificaciones para el cliente.
        Para mostrar badges o indicadores en la UI.
        """
        todas = self.obtener_notificaciones_cliente(cliente_id)
        
        urgentes = [n for n in todas if n.prioridad == PrioridadNotificacion.URGENTE]
        altas = [n for n in todas if n.prioridad == PrioridadNotificacion.ALTA]
        
        return {
            "total": len(todas),
            "urgentes": len(urgentes),
            "altas": len(altas),
            "requiere_atencion": len(urgentes) > 0,
            "tipos": {
                "cuotas_vencidas": len([n for n in todas if n.tipo == TipoNotificacion.CUOTA_VENCIDA]),
                "cuotas_proximas": len([n for n in todas if n.tipo in [
                    TipoNotificacion.CUOTA_PROXIMA_VENCER, 
                    TipoNotificacion.CUOTA_VENCE_HOY
                ]]),
                "prestamos_mora": len([n for n in todas if n.tipo == TipoNotificacion.PRESTAMO_EN_MORA]),
                "solicitudes_pendientes": len([n for n in todas if n.tipo == TipoNotificacion.NUEVA_SOLICITUD]),
            }
        }
    
    def obtener_alertas_dashboard(self) -> List[Notificacion]:
        """
        Obtiene alertas globales para el dashboard de administración.
        Incluye todas las notificaciones urgentes de todos los clientes.
        """
        notificaciones = []
        
        # Cuotas vencidas de todos los clientes
        cuotas_vencidas = PlanPago.objects.filter(
            estado="Vencida"
        ).select_related('prestamo__solicitud__cliente')
        
        for cuota in cuotas_vencidas:
            notificaciones.extend(self.generar_notificaciones_cuota(cuota))
        
        # Cuotas próximas a vencer (7 días)
        fecha_limite = self.hoy + timedelta(days=7)
        cuotas_proximas = PlanPago.objects.filter(
            estado="Pendiente",
            fecha_vencimiento__range=(self.hoy, fecha_limite)
        ).select_related('prestamo__solicitud__cliente')
        
        for cuota in cuotas_proximas:
            notificaciones.extend(self.generar_notificaciones_cuota(cuota))
        
        # Préstamos en mora
        prestamos_mora = Prestamo.objects.filter(
            estado="Mora"
        ).select_related('solicitud__cliente')
        
        for prestamo in prestamos_mora:
            notificaciones.extend(self.generar_notificaciones_prestamo(prestamo))
        
        # Ordenar por prioridad
        prioridad_orden = {
            PrioridadNotificacion.URGENTE: 0,
            PrioridadNotificacion.ALTA: 1,
            PrioridadNotificacion.MEDIA: 2,
            PrioridadNotificacion.BAJA: 3,
        }
        
        notificaciones.sort(key=lambda n: prioridad_orden.get(n.prioridad, 2))
        
        return notificaciones


# Instancia global del servicio (singleton)
notificacion_service = NotificacionService()
