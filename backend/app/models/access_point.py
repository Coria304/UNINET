"""Access Point Wi-Fi físico del campus (RF002, RF005, RF007)."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampsMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.alerta import Alerta
    from app.models.ubicacion import Aula


class BandaFrecuencia(str, enum.Enum):
    GHZ_2_4 = "2.4_GHz"
    GHZ_5 = "5_GHz"
    DUAL = "dual"


class AccessPoint(UUIDPrimaryKeyMixin, TimestampsMixin, Base):
    __tablename__ = "access_points"

    codigo: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    modelo: Mapped[str | None] = mapped_column(String(100), nullable=True)
    mac_address: Mapped[str | None] = mapped_column(String(17), nullable=True, unique=True)
    aula_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("aulas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    banda: Mapped[BandaFrecuencia] = mapped_column(
        Enum(BandaFrecuencia, name="banda_frecuencia"),
        nullable=False,
        default=BandaFrecuencia.DUAL,
    )
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    aula: Mapped[Aula | None] = relationship(back_populates="access_points")
    alertas: Mapped[list[Alerta]] = relationship(back_populates="access_point")
