"""Tickets de incidencias y su historial (RF001, RF004)."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, LargeBinary, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampsMixin, UUIDPrimaryKeyMixin, pg_enum

if TYPE_CHECKING:
    from app.models.alerta import Alerta
    from app.models.usuario import Usuario


class TipoFalla(str, enum.Enum):
    SIN_SENAL = "sin_senal"
    LENTITUD = "lentitud"
    DESCONEXION_INTERMITENTE = "desconexion_intermitente"
    OTRO = "otro"


class EstadoTicket(str, enum.Enum):
    ACTIVO = "activo"
    EN_PROCESO = "en_proceso"
    RESUELTO = "resuelto"


class PrioridadTicket(str, enum.Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


class Ticket(UUIDPrimaryKeyMixin, TimestampsMixin, Base):
    __tablename__ = "tickets"

    reportante_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    asignado_a_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Ubicación pública (visible en reportes anonimizados — RNF008).
    edificio_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("edificios.id"),
        nullable=False,
    )
    piso_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("pisos.id"),
        nullable=True,
    )
    aula_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("aulas.id"),
        nullable=True,
    )

    # Coordenadas GPS exactas: cifradas con pgcrypto (RNF008).
    gps_cifrado: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    # Geohash truncado (~edificio) en claro para búsquedas/duplicados.
    geohash: Mapped[str | None] = mapped_column(String(12), nullable=True, index=True)

    tipo_falla: Mapped[TipoFalla] = mapped_column(
        pg_enum(TipoFalla, name="tipo_falla"), nullable=False
    )
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[EstadoTicket] = mapped_column(
        pg_enum(EstadoTicket, name="estado_ticket"),
        nullable=False,
        default=EstadoTicket.ACTIVO,
        index=True,
    )
    prioridad: Mapped[PrioridadTicket] = mapped_column(
        pg_enum(PrioridadTicket, name="prioridad_ticket"),
        nullable=False,
        default=PrioridadTicket.MEDIA,
    )
    alerta_origen_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("alertas.id", ondelete="SET NULL"),
        nullable=True,
    )
    cerrado_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    reportante: Mapped[Usuario] = relationship(
        back_populates="tickets_reportados",
        foreign_keys=[reportante_id],
    )
    asignado_a: Mapped[Usuario | None] = relationship(
        back_populates="tickets_asignados",
        foreign_keys=[asignado_a_id],
    )
    historico: Mapped[list[TicketHistorico]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketHistorico.fecha",
    )
    alerta_origen: Mapped[Alerta | None] = relationship(back_populates="ticket")


class TicketHistorico(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ticket_historico"

    ticket_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    responsable_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    estado_anterior: Mapped[EstadoTicket | None] = mapped_column(
        pg_enum(EstadoTicket, name="estado_ticket"), nullable=True
    )
    estado_nuevo: Mapped[EstadoTicket] = mapped_column(
        pg_enum(EstadoTicket, name="estado_ticket"), nullable=False
    )
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    ticket: Mapped[Ticket] = relationship(back_populates="historico")
