"""Schemas Pydantic para representar usuarios en la API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.models.usuario import RolUsuario

_ROLES_CREABLES = {RolUsuario.PERSONAL_TECNICO, RolUsuario.ESTUDIANTE, RolUsuario.DOCENTE}

_DOMINIO_ROL: dict[RolUsuario, str] = {
    RolUsuario.ESTUDIANTE: "@alumno.ipn.mx",
    RolUsuario.DOCENTE:    "@docente.ipn.mx",
}


class UsuarioOut(BaseModel):
    """Representación pública de un usuario."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    correo: EmailStr
    nombre_completo: str
    rol: RolUsuario
    activo: bool
    last_login_at: datetime | None = None


class UsuarioCreate(BaseModel):
    """Payload para que el admin dé de alta un nuevo usuario."""

    correo: EmailStr
    nombre_completo: str = Field(min_length=2, max_length=200)
    password: str = Field(min_length=8, max_length=200)
    rol: RolUsuario

    @field_validator("rol")
    @classmethod
    def rol_permitido(cls, v: RolUsuario) -> RolUsuario:
        if v not in _ROLES_CREABLES:
            raise ValueError("Solo se pueden crear usuarios con rol técnico, estudiante o docente")
        return v

    @model_validator(mode="after")
    def correo_institucional(self) -> "UsuarioCreate":
        dominio = _DOMINIO_ROL.get(self.rol)
        if dominio and not str(self.correo).lower().endswith(dominio):
            raise ValueError(
                f"El correo de {self.rol.value} debe terminar en {dominio}"
            )
        return self
