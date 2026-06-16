"""Schemas Pydantic para alertas de saturación (RF003)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.alerta import EstadoAlerta, TipoAlerta


class AlertaOut(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: UUID
    access_point_id: UUID
    ap_codigo: str
    ap_nombre: str
    edificio_codigo: str | None
    tipo: TipoAlerta
    estado: EstadoAlerta
    umbral_violado: float
    valor_observado: float
    detectada_at: datetime
    atendida_at: datetime | None
    comentario_resolucion: str | None


class AlertaAtenderIn(BaseModel):
    comentario_resolucion: str | None = None
