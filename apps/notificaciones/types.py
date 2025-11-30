"""
Definición de tipos y estructuras para el sistema de notificaciones.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Literal
from enum import Enum


class TipoNotificacion(str, Enum):
    """
    Tipos de notificaciones disponibles en el sistema.
    """
    # Notificaciones de Solicitudes
    NUEVA_SOLICITUD = "nueva_solicitud"
    SOLICITUD_APROBADA = "solicitud_aprobada"
    SOLICITUD_RECHAZADA = "solicitud_rechazada"
    CAMBIO_ESTADO_SOLICITUD = "cambio_estado_solicitud"
    
    # Notificaciones de Préstamos
    PRESTAMO_APROBADO = "prestamo_aprobado"
    PRESTAMO_DESEMBOLSADO = "prestamo_desembolsado"
    CAMBIO_ESTADO_PRESTAMO = "cambio_estado_prestamo"
    PRESTAMO_EN_MORA = "prestamo_en_mora"
    PRESTAMO_COMPLETADO = "prestamo_completado"
    
    # Notificaciones de Plan de Pagos
    RECORDATORIO_CUOTA = "recordatorio_cuota"
    CUOTA_PROXIMA_VENCER = "cuota_proxima_vencer"
    CUOTA_VENCE_HOY = "cuota_vence_hoy"
    CUOTA_VENCIDA = "cuota_vencida"
    PAGO_COMPLETADO = "pago_completado"
    MORA_ACUMULADA = "mora_acumulada"
    
    # Notificaciones Generales
    ADVERTENCIA = "advertencia"
    INFORMATIVA = "informativa"


class CategoriaNotificacion(str, Enum):
    """
    Categorías
    """
    EMERGENTE = "emergente"       # Alerta popup que debe mostrarse inmediatamente
    PERSISTENTE = "persistente"   # Aparece en el historial/lista de notificaciones
    AMBAS = "ambas"               # Se muestra como emergente Y queda en historial


class PrioridadNotificacion(str, Enum):
    """
    Niveles de prioridad
    """
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    URGENTE = "urgente"


class EstiloNotificacion(str, Enum):
    """
    Estilos visuales para las notificaciones emergentes.
    """
    INFO = "info"           # Informativa - color azul
    SUCCESS = "success"     # Éxito - color verde  
    WARNING = "warning"     # Advertencia - color amarillo/naranja
    ERROR = "error"         # Error/Urgente - color rojo
    REMINDER = "reminder"   # Recordatorio - color morado


@dataclass
class Notificacion:
    """
    Estructura de datos para una notificación de cliente.
    """
    # Identificación
    id: str                                     # ID único generado
    tipo: TipoNotificacion                      # Tipo de notificación
    categoria: CategoriaNotificacion            # Comportamiento (emergente/persistente/ambas)
    
    # Contenido
    titulo: str                                 # Título corto y descriptivo
    mensaje: str                                # Mensaje detallado para el cliente
    
    # Relaciones (IDs de objetos relacionados)
    cliente_id: int                             # ID del cliente destinatario
    solicitud_id: Optional[int] = None          # ID de solicitud relacionada
    prestamo_id: Optional[int] = None           # ID de préstamo relacionado
    plan_pago_id: Optional[int] = None          # ID de cuota relacionada
    
    # Metadata
    prioridad: PrioridadNotificacion = PrioridadNotificacion.MEDIA
    estilo: EstiloNotificacion = EstiloNotificacion.INFO
    fecha_generacion: datetime = field(default_factory=datetime.now)
    fecha_evento: Optional[date] = None         # Fecha del evento (ej: vencimiento)
    
    # Estado
    leida: bool = False
    
    # Datos adicionales (para mostrar en la UI)
    datos_extra: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convierte la notificación a diccionario para serialización."""
        return {
            "id": self.id,
            "tipo": self.tipo.value,
            "categoria": self.categoria.value,
            "titulo": self.titulo,
            "mensaje": self.mensaje,
            "cliente_id": self.cliente_id,
            "solicitud_id": self.solicitud_id,
            "prestamo_id": self.prestamo_id,
            "plan_pago_id": self.plan_pago_id,
            "prioridad": self.prioridad.value,
            "estilo": self.estilo.value,
            "fecha_generacion": self.fecha_generacion.isoformat(),
            "fecha_evento": self.fecha_evento.isoformat() if self.fecha_evento else None,
            "leida": self.leida,
            "datos_extra": self.datos_extra,
        }


@dataclass  
class ConfiguracionNotificacion:
    """
    Configuración para la generación automática de notificaciones.
    """
    # Recordatorios de cuotas
    dias_anticipacion_recordatorio: int = 7    # Días antes del vencimiento
    dias_anticipacion_urgente: int = 3         # Días antes para urgencia alta
    dias_anticipacion_inmediato: int = 1       # Un día antes
    
    # Configuración de mora
    mostrar_mora_desde_dias: int = 1           # Mostrar mora desde el primer día
    intervalo_recordatorio_mora_dias: int = 3  # Recordar mora cada X días
    
    # Intervalos de actualización (en minutos)
    intervalo_actualizacion_cuotas: int = 60   # Cada hora verificar cuotas
    
    def to_dict(self) -> dict:
        return {
            "dias_anticipacion_recordatorio": self.dias_anticipacion_recordatorio,
            "dias_anticipacion_urgente": self.dias_anticipacion_urgente,
            "dias_anticipacion_inmediato": self.dias_anticipacion_inmediato,
            "mostrar_mora_desde_dias": self.mostrar_mora_desde_dias,
            "intervalo_recordatorio_mora_dias": self.intervalo_recordatorio_mora_dias,
            "intervalo_actualizacion_cuotas": self.intervalo_actualizacion_cuotas,
        }


# Mapeo de tipos de notificación a configuraciones predeterminadas
CONFIGURACION_POR_TIPO = {
    # Solicitudes
    TipoNotificacion.NUEVA_SOLICITUD: {
        "categoria": CategoriaNotificacion.AMBAS,
        "prioridad": PrioridadNotificacion.MEDIA,
        "estilo": EstiloNotificacion.INFO,
    },
    TipoNotificacion.SOLICITUD_APROBADA: {
        "categoria": CategoriaNotificacion.AMBAS,
        "prioridad": PrioridadNotificacion.ALTA,
        "estilo": EstiloNotificacion.SUCCESS,
    },
    TipoNotificacion.SOLICITUD_RECHAZADA: {
        "categoria": CategoriaNotificacion.AMBAS,
        "prioridad": PrioridadNotificacion.ALTA,
        "estilo": EstiloNotificacion.WARNING,
    },
    
    # Préstamos
    TipoNotificacion.PRESTAMO_APROBADO: {
        "categoria": CategoriaNotificacion.AMBAS,
        "prioridad": PrioridadNotificacion.ALTA,
        "estilo": EstiloNotificacion.SUCCESS,
    },
    TipoNotificacion.PRESTAMO_DESEMBOLSADO: {
        "categoria": CategoriaNotificacion.AMBAS,
        "prioridad": PrioridadNotificacion.ALTA,
        "estilo": EstiloNotificacion.SUCCESS,
    },
    TipoNotificacion.PRESTAMO_EN_MORA: {
        "categoria": CategoriaNotificacion.AMBAS,
        "prioridad": PrioridadNotificacion.URGENTE,
        "estilo": EstiloNotificacion.ERROR,
    },
    TipoNotificacion.PRESTAMO_COMPLETADO: {
        "categoria": CategoriaNotificacion.AMBAS,
        "prioridad": PrioridadNotificacion.ALTA,
        "estilo": EstiloNotificacion.SUCCESS,
    },
    
    # Plan de pagos
    TipoNotificacion.RECORDATORIO_CUOTA: {
        "categoria": CategoriaNotificacion.EMERGENTE,
        "prioridad": PrioridadNotificacion.MEDIA,
        "estilo": EstiloNotificacion.REMINDER,
    },
    TipoNotificacion.CUOTA_PROXIMA_VENCER: {
        "categoria": CategoriaNotificacion.AMBAS,
        "prioridad": PrioridadNotificacion.ALTA,
        "estilo": EstiloNotificacion.WARNING,
    },
    TipoNotificacion.CUOTA_VENCE_HOY: {
        "categoria": CategoriaNotificacion.AMBAS,
        "prioridad": PrioridadNotificacion.URGENTE,
        "estilo": EstiloNotificacion.WARNING,
    },
    TipoNotificacion.CUOTA_VENCIDA: {
        "categoria": CategoriaNotificacion.AMBAS,
        "prioridad": PrioridadNotificacion.URGENTE,
        "estilo": EstiloNotificacion.ERROR,
    },
    TipoNotificacion.PAGO_COMPLETADO: {
        "categoria": CategoriaNotificacion.AMBAS,
        "prioridad": PrioridadNotificacion.MEDIA,
        "estilo": EstiloNotificacion.SUCCESS,
    },
    TipoNotificacion.MORA_ACUMULADA: {
        "categoria": CategoriaNotificacion.AMBAS,
        "prioridad": PrioridadNotificacion.URGENTE,
        "estilo": EstiloNotificacion.ERROR,
    },
    
    # Generales
    TipoNotificacion.ADVERTENCIA: {
        "categoria": CategoriaNotificacion.EMERGENTE,
        "prioridad": PrioridadNotificacion.ALTA,
        "estilo": EstiloNotificacion.WARNING,
    },
    TipoNotificacion.INFORMATIVA: {
        "categoria": CategoriaNotificacion.PERSISTENTE,
        "prioridad": PrioridadNotificacion.BAJA,
        "estilo": EstiloNotificacion.INFO,
    },
}
