"""Series temporales de monitoreo de APs (RF002).

Esta tabla se convierte en hypertable de TimescaleDB en la migración
inicial. La PK compuesta incluye `ts` para que la partición por tiempo
funcione correctamente.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, Integer, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MetricaMonitoreo(Base):
    __tablename__ = "metricas_monitoreo"
    __table_args__ = (PrimaryKeyConstraint("ts", "access_point_id", name="pk_metricas_monitoreo"),)

    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    access_point_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("access_points.id", ondelete="CASCADE"),
        nullable=False,
    )
    ancho_banda_mbps: Mapped[float] = mapped_column(Float, nullable=False)
    latencia_ms: Mapped[float] = mapped_column(Float, nullable=False)
    carga_pct: Mapped[float] = mapped_column(Float, nullable=False)
    paquetes_perdidos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clientes_conectados: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
