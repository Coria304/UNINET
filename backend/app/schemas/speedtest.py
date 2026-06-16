from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SpeedtestResultadoIn(BaseModel):
    velocidad_bajada_mbps: float = Field(ge=0)
    velocidad_subida_mbps: float = Field(ge=0)
    latencia_ms: float = Field(ge=0)
    edificio_id: UUID | None = None
    piso_id: UUID | None = None
    aula_id: UUID | None = None


class SpeedtestResultadoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    usuario_id: UUID
    edificio_id: UUID | None
    piso_id: UUID | None
    aula_id: UUID | None
    velocidad_bajada_mbps: float
    velocidad_subida_mbps: float
    latencia_ms: float
    ip_origen: str | None
    ejecutado_at: datetime
