"""Schemas Pydantic de la jerarquía física: Edificio → Piso → Aula (RF001)."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AulaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    codigo: str
    nombre: str | None = None
    tipo: str | None = None


class PisoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    numero: int
    nombre: str
    aulas: list[AulaOut] = []


class EdificioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    codigo: str
    nombre: str
    descripcion: str | None = None
    latitud: float | None = None
    longitud: float | None = None


class EdificioConPisos(EdificioOut):
    """Edificio con árbol completo cargado — payload del mapa del portal."""

    pisos: list[PisoOut] = []
