"""Alertas automáticas de saturación y caída de nodos (RF003)."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampsMixin, UUIDPrimaryKeyMixin, pg_enum

if TYPE_CHECKING:
    from app.models.access_point import AccessPoint
    from app.models.ticket import Ticket


class TipoAlerta(str, enum.Enum):
    SATURACION_CARGA = "saturacion_carga"
    LATENCIA_ALTA = "latencia_alta"
    NODO_CAIDO = "nodo_caido"


class EstadoAlerta(str, enum.Enum):
    ACTIVA = "activa"
    ATENDIDA = "atendida"
    CERRADA_AUTO = "cerrada_auto"
    ESCALADA = "escalada"


class Alerta(UUIDPrimaryKeyMixin, TimestampsMixin, Base):
    __tablename__ = "alertas"

    access_point_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("access_points.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tipo: Mapped[TipoAlerta] = mapped_column(
        pg_enum(TipoAlerta, name="tipo_alerta"), nullable=False
    )
    estado: Mapped[EstadoAlerta] = mapped_column(
        pg_enum(EstadoAlerta, name="estado_alerta"),
        nullable=False,
        default=EstadoAlerta.ACTIVA,
        index=True,
    )
    umbral_violado: Mapped[float] = mapped_column(Float, nullable=False)
    valor_observado: Mapped[float] = mapped_column(Float, nullable=False)
    detectada_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    atendida_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    atendida_por_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    comentario_resolucion: Mapped[str | None] = mapped_column(String(500), nullable=True)

    access_point: Mapped[AccessPoint] = relationship(back_populates="alertas")
    ticket: Mapped[Ticket | None] = relationship(back_populates="alerta_origen", uselist=False)
