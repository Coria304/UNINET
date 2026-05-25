"""Schemas Pydantic del flujo de tickets (RF001, RF004)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.ticket import EstadoTicket, PrioridadTicket, TipoFalla
from app.schemas.usuario import UsuarioOut


class TicketCreate(BaseModel):
    """Reporte que envía un estudiante o docente desde el portal."""

    edificio_id: UUID
    piso_id: UUID | None = None
    aula_id: UUID | None = None
    tipo_falla: TipoFalla
    descripcion: str | None = Field(default=None, max_length=2000)

    # GPS opcional. En Sprint 2 sólo derivamos un geohash para búsqueda;
    # el cifrado con pgcrypto (RNF008) llega en Sprint 5 (endurecimiento).
    latitud: float | None = Field(default=None, ge=-90, le=90)
    longitud: float | None = Field(default=None, ge=-180, le=180)


class TicketUpdate(BaseModel):
    """Cambios que aplica un técnico o admin sobre un ticket existente."""

    estado: EstadoTicket | None = None
    asignado_a_id: UUID | None = None
    prioridad: PrioridadTicket | None = None
    comentario: str | None = Field(default=None, max_length=2000)


class TicketHistoricoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    estado_anterior: EstadoTicket | None = None
    estado_nuevo: EstadoTicket
    comentario: str | None = None
    responsable_id: UUID | None = None
    fecha: datetime


class TicketListItem(BaseModel):
    """Vista compacta para listados (sin historial, sin relaciones cargadas)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tipo_falla: TipoFalla
    estado: EstadoTicket
    prioridad: PrioridadTicket
    edificio_id: UUID
    piso_id: UUID | None = None
    aula_id: UUID | None = None
    reportante_id: UUID
    asignado_a_id: UUID | None = None
    descripcion: str | None = None
    geohash: str | None = None
    created_at: datetime
    cerrado_at: datetime | None = None


class TicketOut(BaseModel):
    """Detalle completo de un ticket incluyendo historial."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reportante: UsuarioOut
    asignado_a: UsuarioOut | None = None

    edificio_id: UUID
    piso_id: UUID | None = None
    aula_id: UUID | None = None

    tipo_falla: TipoFalla
    descripcion: str | None = None
    estado: EstadoTicket
    prioridad: PrioridadTicket
    geohash: str | None = None

    created_at: datetime
    updated_at: datetime
    cerrado_at: datetime | None = None

    historico: list[TicketHistoricoOut] = []
