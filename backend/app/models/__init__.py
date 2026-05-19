"""Entidades de dominio de UniNet Connect.

Importar desde aquí garantiza que Alembic detecte todos los modelos
para autogeneración de migraciones.
"""

from app.models.access_point import AccessPoint, BandaFrecuencia
from app.models.alerta import Alerta, EstadoAlerta, TipoAlerta
from app.models.audit_log import AuditLog
from app.models.base import Base
from app.models.configuracion import ConfiguracionUmbrales
from app.models.metrica import MetricaMonitoreo
from app.models.reporte import ReporteSLA, TipoReporte
from app.models.speedtest import SpeedtestResultado
from app.models.ticket import (
    EstadoTicket,
    PrioridadTicket,
    Ticket,
    TicketHistorico,
    TipoFalla,
)
from app.models.ubicacion import Aula, Edificio, Piso
from app.models.usuario import RolUsuario, Usuario

__all__ = [
    "AccessPoint",
    "Alerta",
    "Aula",
    "AuditLog",
    "BandaFrecuencia",
    "Base",
    "ConfiguracionUmbrales",
    "Edificio",
    "EstadoAlerta",
    "EstadoTicket",
    "MetricaMonitoreo",
    "Piso",
    "PrioridadTicket",
    "ReporteSLA",
    "RolUsuario",
    "SpeedtestResultado",
    "Ticket",
    "TicketHistorico",
    "TipoAlerta",
    "TipoFalla",
    "TipoReporte",
    "Usuario",
]
