"""Jerarquía física del campus: Edificio → Piso → Aula (RF001, RF005)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampsMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.access_point import AccessPoint


class Edificio(UUIDPrimaryKeyMixin, TimestampsMixin, Base):
    __tablename__ = "edificios"

    codigo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Centroide del edificio (no es ubicación sensible del usuario).
    latitud: Mapped[float | None] = mapped_column(nullable=True)
    longitud: Mapped[float | None] = mapped_column(nullable=True)

    pisos: Mapped[list[Piso]] = relationship(
        back_populates="edificio",
        cascade="all, delete-orphan",
    )


class Piso(UUIDPrimaryKeyMixin, TimestampsMixin, Base):
    __tablename__ = "pisos"
    __table_args__ = (UniqueConstraint("edificio_id", "numero", name="piso_unico_por_edificio"),)

    edificio_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("edificios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    numero: Mapped[int] = mapped_column(Integer, nullable=False)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)

    edificio: Mapped[Edificio] = relationship(back_populates="pisos")
    aulas: Mapped[list[Aula]] = relationship(
        back_populates="piso",
        cascade="all, delete-orphan",
    )


class Aula(UUIDPrimaryKeyMixin, TimestampsMixin, Base):
    __tablename__ = "aulas"
    __table_args__ = (UniqueConstraint("piso_id", "codigo", name="aula_unica_por_piso"),)

    piso_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("pisos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    codigo: Mapped[str] = mapped_column(String(40), nullable=False)
    nombre: Mapped[str | None] = mapped_column(String(150), nullable=True)
    tipo: Mapped[str | None] = mapped_column(String(50), nullable=True)  # aula, lab, area_comun

    piso: Mapped[Piso] = relationship(back_populates="aulas")
    access_points: Mapped[list[AccessPoint]] = relationship(back_populates="aula")
