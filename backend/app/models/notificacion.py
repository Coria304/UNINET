"""Notificaciones in-app y por correo (RF005)."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin, pg_enum

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class TipoNotificacion(str, enum.Enum):
    TICKET_CREADO = "ticket_creado"
    TICKET_ASIGNADO = "ticket_asignado"
    TICKET_ESTADO_CAMBIO = "ticket_estado_cambio"


class Notificacion(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "notificaciones"

    usuario_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tipo: Mapped[TipoNotificacion] = mapped_column(
        pg_enum(TipoNotificacion, name="tipo_notificacion"), nullable=False
    )
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    mensaje: Mapped[str] = mapped_column(Text, nullable=False)

    # Referencia opcional a una entidad — habilita deep-linking desde la UI.
    entidad_tipo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entidad_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    leida: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    leida_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    usuario: Mapped[Usuario] = relationship(back_populates="notificaciones")
