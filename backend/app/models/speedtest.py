"""Resultados del speedtest integrado (RF008)."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class SpeedtestResultado(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "speedtest_resultados"

    usuario_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    edificio_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("edificios.id", ondelete="SET NULL"), nullable=True
    )
    piso_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("pisos.id", ondelete="SET NULL"), nullable=True
    )
    aula_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("aulas.id", ondelete="SET NULL"), nullable=True
    )
    velocidad_bajada_mbps: Mapped[float] = mapped_column(Float, nullable=False)
    velocidad_subida_mbps: Mapped[float] = mapped_column(Float, nullable=False)
    latencia_ms: Mapped[float] = mapped_column(Float, nullable=False)
    ip_origen: Mapped[str | None] = mapped_column(String(45), nullable=True)
    ejecutado_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
