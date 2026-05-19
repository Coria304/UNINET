"""Configuración de umbrales del sistema de alertas (RF003)."""

from uuid import UUID

from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampsMixin, UUIDPrimaryKeyMixin


class ConfiguracionUmbrales(UUIDPrimaryKeyMixin, TimestampsMixin, Base):
    """Configuración global de umbrales (una única fila esperada por entorno)."""

    __tablename__ = "configuracion_umbrales"

    carga_pct: Mapped[float] = mapped_column(Float, nullable=False, default=80.0)
    latencia_ms: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    duracion_minima_seg: Mapped[int] = mapped_column(Integer, nullable=False, default=120)
    actualizado_por_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
