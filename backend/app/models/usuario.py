"""Usuario institucional con rol (RF009, RNF001)."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampsMixin, UUIDPrimaryKeyMixin, pg_enum

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.ticket import Ticket


class RolUsuario(str, enum.Enum):
    ADMINISTRADOR_TI = "administrador_ti"
    PERSONAL_TECNICO = "personal_tecnico"
    DOCENTE = "docente"
    ESTUDIANTE = "estudiante"


class Usuario(UUIDPrimaryKeyMixin, TimestampsMixin, Base):
    __tablename__ = "usuarios"

    correo: Mapped[str] = mapped_column(CITEXT, unique=True, nullable=False, index=True)
    nombre_completo: Mapped[str] = mapped_column(String(200), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[RolUsuario] = mapped_column(
        pg_enum(RolUsuario, name="rol_usuario"),
        nullable=False,
        index=True,
    )
    mfa_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # --- Estado del flujo de autenticación (RF009, RNF001) ---
    failed_login_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    tickets_reportados: Mapped[list[Ticket]] = relationship(
        back_populates="reportante",
        foreign_keys="Ticket.reportante_id",
    )
    tickets_asignados: Mapped[list[Ticket]] = relationship(
        back_populates="asignado_a",
        foreign_keys="Ticket.asignado_a_id",
    )
    audit_logs: Mapped[list[AuditLog]] = relationship(back_populates="usuario")
