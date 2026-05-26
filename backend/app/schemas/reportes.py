"""Schemas Pydantic para reportes agregados (RF007).

Vistas de agregación sobre tickets. Sirven al dashboard administrativo y
sientan la base para los `ReporteSLA` persistidos (Sprint 5).
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.ticket import EstadoTicket, TipoFalla


class ContadorPorEstado(BaseModel):
    activo: int = 0
    en_proceso: int = 0
    resuelto: int = 0


class BucketEdificio(BaseModel):
    edificio_id: UUID
    codigo: str
    nombre: str
    total: int


class BucketTipoFalla(BaseModel):
    tipo: TipoFalla
    total: int


class PuntoSerieTemporal(BaseModel):
    """Un punto de la serie. `fecha` es el inicio del bucket (día/semana/mes)."""

    fecha: datetime
    total: int


class ResumenReporte(BaseModel):
    """Snapshot agregado del rango consultado."""

    model_config = ConfigDict(use_enum_values=True)

    desde: datetime
    hasta: datetime
    total: int
    por_estado: ContadorPorEstado
    mttr_horas: float | None  # null si no hay tickets resueltos en el rango
    sin_asignar: int
    top_edificios: list[BucketEdificio]
    top_tipos: list[BucketTipoFalla]
    serie_temporal: list[PuntoSerieTemporal]
    granularidad: str  # "day" | "week" | "month"


class FiltroRango(BaseModel):
    """No se valida en endpoint; documenta los parámetros aceptados."""

    desde: datetime | None = None
    hasta: datetime | None = None
    granularidad: str = "day"  # día por defecto

    @classmethod
    def map_granularidad(cls, valor: str) -> str:
        mapa = {"dia": "day", "semana": "week", "mes": "month"}
        return mapa.get(valor.lower(), valor.lower())


class _EstadoBucketRow(BaseModel):
    """Estructura interna usada para construir ContadorPorEstado."""

    estado: EstadoTicket
    total: int
