"""Registro de auditoría de acciones críticas (RNF010, LFPDPPP)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class AuditLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "audit_log"

    usuario_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    accion: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entidad: Mapped[str | None] = mapped_column(String(100), nullable=True)
    entidad_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    datos: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_origen: Mapped[str | None] = mapped_column(INET, nullable=True)
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    usuario: Mapped[Usuario | None] = relationship(back_populates="audit_logs")
