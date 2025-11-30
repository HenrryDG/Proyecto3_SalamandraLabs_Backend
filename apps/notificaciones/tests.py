"""
Tests para el sistema de notificaciones.
"""

from django.test import TestCase
from datetime import date, timedelta
from decimal import Decimal

from apps.clientes.models import Cliente
from apps.solicitudes.models import SolicitudPrestamo
from apps.prestamos.models import Prestamo
from apps.plan_pagos.models import PlanPago

from .services import NotificacionService
from .types import (
    TipoNotificacion,
    CategoriaNotificacion,
    PrioridadNotificacion,
)


class NotificacionServiceTestCase(TestCase):
    """Tests para el servicio de notificaciones."""
    
    def setUp(self):
        """Configuración inicial para los tests."""
        self.service = NotificacionService()
    
    def test_crear_servicio(self):
        """Test de creación del servicio."""
        self.assertIsNotNone(self.service)
        self.assertIsNotNone(self.service.config)
    
    def test_configuracion_por_defecto(self):
        """Test de configuración por defecto."""
        config = self.service.config
        self.assertEqual(config.dias_anticipacion_recordatorio, 7)
        self.assertEqual(config.dias_anticipacion_urgente, 3)
        self.assertEqual(config.dias_anticipacion_inmediato, 1)


class TiposNotificacionTestCase(TestCase):
    """Tests para los tipos de notificación."""
    
    def test_tipos_notificacion_definidos(self):
        """Verificar que todos los tipos estén definidos."""
        tipos_esperados = [
            'NUEVA_SOLICITUD',
            'SOLICITUD_APROBADA',
            'SOLICITUD_RECHAZADA',
            'PRESTAMO_APROBADO',
            'PRESTAMO_EN_MORA',
            'PRESTAMO_COMPLETADO',
            'RECORDATORIO_CUOTA',
            'CUOTA_VENCIDA',
            'PAGO_COMPLETADO',
        ]
        
        for tipo in tipos_esperados:
            self.assertTrue(
                hasattr(TipoNotificacion, tipo),
                f"Tipo {tipo} no encontrado en TipoNotificacion"
            )
    
    def test_categorias_definidas(self):
        """Verificar categorías de notificación."""
        self.assertEqual(CategoriaNotificacion.EMERGENTE.value, "emergente")
        self.assertEqual(CategoriaNotificacion.PERSISTENTE.value, "persistente")
        self.assertEqual(CategoriaNotificacion.AMBAS.value, "ambas")
    
    def test_prioridades_definidas(self):
        """Verificar prioridades de notificación."""
        self.assertEqual(PrioridadNotificacion.BAJA.value, "baja")
        self.assertEqual(PrioridadNotificacion.MEDIA.value, "media")
        self.assertEqual(PrioridadNotificacion.ALTA.value, "alta")
        self.assertEqual(PrioridadNotificacion.URGENTE.value, "urgente")
