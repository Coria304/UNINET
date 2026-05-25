"""Servicio de autenticación.

Orquesta el flujo de login (con bloqueo y MFA) y el de verificación MFA.
Lanza `AuthError` para que la capa de API la traduzca a HTTP.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, verify_password
from app.models import RolUsuario, Usuario
from app.repositories.usuario import UsuarioRepository
from app.services import audit, mfa

# Configuración de bloqueo según CA-RF009-2.
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=15)

# Roles que requieren MFA según CA-RF009-3.
ROLES_QUE_REQUIEREN_MFA = frozenset({RolUsuario.ADMINISTRADOR_TI})


class AuthErrorCode(str, Enum):
    INVALID_CREDENTIALS = "invalid_credentials"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_INACTIVE = "account_inactive"
    INVALID_MFA_CODE = "invalid_mfa_code"
    MFA_CHALLENGE_EXPIRED = "mfa_challenge_expired"


class AuthError(Exception):
    def __init__(self, code: AuthErrorCode, retry_after_seconds: int | None = None) -> None:
        super().__init__(code.value)
        self.code = code
        self.retry_after_seconds = retry_after_seconds


@dataclass
class LoginOutcome:
    """Resultado de un login: o requiere MFA, o emite token directamente."""

    usuario: Usuario
    requires_mfa: bool
    challenge_id: UUID | None = None
    dev_code: str | None = None
    access_token: str | None = None


def authenticate(db: Session, *, correo: str, password: str, ip: str | None) -> LoginOutcome:
    """Valida credenciales, gestiona bloqueo e inicia MFA si corresponde."""
    repo = UsuarioRepository(db)
    usuario = repo.get_by_correo(correo)

    if usuario is None:
        # No exponemos si el correo existe (mismo error que password incorrecto).
        audit.record_event(
            db,
            accion="login_failed",
            datos={"correo": correo, "motivo": "usuario_inexistente"},
            ip_origen=ip,
        )
        raise AuthError(AuthErrorCode.INVALID_CREDENTIALS)

    _ensure_not_locked(usuario)

    if not usuario.activo:
        raise AuthError(AuthErrorCode.ACCOUNT_INACTIVE)

    if not verify_password(password, usuario.password_hash):
        repo.register_failed_attempt(
            usuario,
            max_attempts=MAX_FAILED_ATTEMPTS,
            lockout_duration=LOCKOUT_DURATION,
        )
        audit.record_event(
            db,
            accion="login_failed",
            usuario_id=usuario.id,
            datos={
                "motivo": "password_incorrecto",
                "intentos": usuario.failed_login_attempts,
            },
            ip_origen=ip,
        )
        db.commit()
        # Nota: aunque este intento haya disparado el bloqueo, devolvemos
        # 401 (no 423). El bloqueo se reportará al siguiente intento, como
        # exige CA-RF009-2 ("5 intentos fallidos consecutivos, cuando
        # intenta autenticarse nuevamente, el sistema bloquea la cuenta").
        raise AuthError(AuthErrorCode.INVALID_CREDENTIALS)

    # Credenciales válidas: limpiar contador y, según rol, exigir MFA.
    repo.reset_after_success(usuario)

    if usuario.rol in ROLES_QUE_REQUIEREN_MFA:
        challenge = mfa.issue_challenge(usuario.id, usuario.correo)
        audit.record_event(
            db,
            accion="login_mfa_pending",
            usuario_id=usuario.id,
            ip_origen=ip,
        )
        db.commit()
        settings = get_settings()
        return LoginOutcome(
            usuario=usuario,
            requires_mfa=True,
            challenge_id=challenge.challenge_id,
            dev_code=None if settings.is_production else challenge.code,
        )

    token = create_access_token(usuario.id, extra_claims={"rol": usuario.rol.value})
    audit.record_event(db, accion="login_success", usuario_id=usuario.id, ip_origen=ip)
    db.commit()
    return LoginOutcome(usuario=usuario, requires_mfa=False, access_token=token)


def verify_mfa(db: Session, *, challenge_id: UUID, code: str, ip: str | None) -> LoginOutcome:
    """Valida el código MFA y, si es correcto, emite el token de acceso."""
    usuario_id = mfa.verify_challenge(challenge_id, code)
    if usuario_id is None:
        audit.record_event(
            db,
            accion="mfa_failed",
            datos={"challenge_id": str(challenge_id)},
            ip_origen=ip,
        )
        db.commit()
        raise AuthError(AuthErrorCode.INVALID_MFA_CODE)

    usuario = db.get(Usuario, usuario_id)
    if usuario is None or not usuario.activo:
        raise AuthError(AuthErrorCode.ACCOUNT_INACTIVE)

    token = create_access_token(usuario.id, extra_claims={"rol": usuario.rol.value})
    audit.record_event(db, accion="mfa_success", usuario_id=usuario.id, ip_origen=ip)
    db.commit()
    return LoginOutcome(usuario=usuario, requires_mfa=False, access_token=token)


def _ensure_not_locked(usuario: Usuario) -> None:
    if usuario.locked_until is None:
        return
    now = datetime.now(timezone.utc)
    if usuario.locked_until > now:
        retry_after = int((usuario.locked_until - now).total_seconds())
        raise AuthError(AuthErrorCode.ACCOUNT_LOCKED, retry_after_seconds=retry_after)
