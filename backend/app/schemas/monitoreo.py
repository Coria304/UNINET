"""Schemas Pydantic para monitoreo en tiempo real (RF002)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.access_point import BandaFrecuencia


class MetricaResumen(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    ts: datetime
    ancho_banda_mbps: float
    latencia_ms: float
    carga_pct: float
    clientes_conectados: int
    estado_semaforo: str  # "good" | "high" | "saturated"


class AccessPointEstado(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: UUID
    codigo: str
    nombre: str
    edificio_id: UUID | None
    edificio_codigo: str | None
    piso_id: UUID | None
    latitud: float | None
    longitud: float | None
    activo: bool
    banda: BandaFrecuencia
    ultima_metrica: MetricaResumen | None


class MonitoreoResponse(BaseModel):
    total: int
    activos: int
    con_alertas: int
    access_points: list[AccessPointEstado]


class MetricaIn(BaseModel):
    access_point_id: UUID
    ancho_banda_mbps: float
    latencia_ms: float
    carga_pct: float
    paquetes_perdidos: int = 0
    clientes_conectados: int = 0
