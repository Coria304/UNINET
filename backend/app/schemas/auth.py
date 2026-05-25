"""Schemas Pydantic para el flujo de autenticación (RF009, CU-10)."""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.schemas.usuario import UsuarioOut


class LoginRequest(BaseModel):
    correo: EmailStr
    password: str = Field(min_length=1, max_length=200)


class LoginResponseToken(BaseModel):
    """Respuesta cuando NO se requiere MFA: token de acceso emitido."""

    mfa_required: bool = False
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut


class LoginResponseMFA(BaseModel):
    """Respuesta cuando SÍ se requiere MFA: reto pendiente, sin token."""

    mfa_required: bool = True
    challenge_id: UUID
    expires_in: int = Field(default=300, description="TTL del reto en segundos.")
    # En entornos no-productivos exponemos el código para facilitar pruebas E2E.
    dev_code: str | None = None


class MFAVerifyRequest(BaseModel):
    challenge_id: UUID
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
