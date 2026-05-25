"""Schemas Pydantic para representar usuarios en la API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.usuario import RolUsuario


class UsuarioOut(BaseModel):
    """Representación pública de un usuario."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    correo: EmailStr
    nombre_completo: str
    rol: RolUsuario
    activo: bool
    last_login_at: datetime | None = None
