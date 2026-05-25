"""Reportes históricos SLA generados (RF006, RF010)."""

import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampsMixin, UUIDPrimaryKeyMixin, pg_enum


class TipoReporte(str, enum.Enum):
    SLA_MENSUAL = "sla_mensual"
    DISPONIBILIDAD_DIARIA = "disponibilidad_diaria"
    INCIDENCIAS = "incidencias"


class ReporteSLA(UUIDPrimaryKeyMixin, TimestampsMixin, Base):
    __tablename__ = "reportes_sla"

    tipo: Mapped[TipoReporte] = mapped_column(
        pg_enum(TipoReporte, name="tipo_reporte"), nullable=False
    )
    rango_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rango_fin: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    edificio_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("edificios.id", ondelete="SET NULL"), nullable=True
    )
    generado_por_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    pdf_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
