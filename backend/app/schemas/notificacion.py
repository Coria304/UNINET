"""Schemas Pydantic de notificaciones (RF005)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.notificacion import TipoNotificacion


class NotificacionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tipo: TipoNotificacion
    titulo: str
    mensaje: str
    entidad_tipo: str | None = None
    entidad_id: str | None = None
    leida: bool
    leida_at: datetime | None = None
    created_at: datetime


class NotificacionListResponse(BaseModel):
    """Listado paginado + contador de no leídas (para badge en UI)."""

    items: list[NotificacionOut]
    total_no_leidas: int
