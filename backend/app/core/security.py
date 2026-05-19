"""Primitivas de seguridad: hashing Argon2, JWT y utilidades MFA.

Estas funciones son la base para Sprint 1 (RF009, RNF001).
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import get_settings

settings = get_settings()
_hasher = PasswordHasher()
_JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Genera un hash Argon2id de la contraseña."""
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verifica una contraseña contra su hash Argon2."""
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def needs_rehash(password_hash: str) -> bool:
    """True si los parámetros de Argon2 deben actualizarse."""
    return _hasher.check_needs_rehash(password_hash)


def create_access_token(
    subject: str | int,
    *,
    extra_claims: dict[str, Any] | None = None,
    expires_minutes: int | None = None,
) -> str:
    """Genera un JWT firmado con HS256."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=_JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decodifica un JWT. Lanza `jwt.PyJWTError` si es inválido o expiró."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[_JWT_ALGORITHM])
