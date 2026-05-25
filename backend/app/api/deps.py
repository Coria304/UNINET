"""Dependencias compartidas para los endpoints FastAPI."""

from collections.abc import Iterable
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import RolUsuario, Usuario

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=True,
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """Decodifica el JWT y devuelve el usuario autenticado."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError as exc:
        raise credentials_exc from exc

    raw_sub = payload.get("sub")
    if not raw_sub:
        raise credentials_exc

    try:
        usuario_id = UUID(raw_sub)
    except (TypeError, ValueError) as exc:
        raise credentials_exc from exc

    usuario = db.get(Usuario, usuario_id)
    if usuario is None or not usuario.activo:
        raise credentials_exc
    return usuario


def require_roles(*roles: RolUsuario):
    """Dependency factory: exige que el usuario tenga uno de los roles dados."""
    allowed: Iterable[RolUsuario] = roles

    def checker(current_user: Usuario = Depends(get_current_user)) -> Usuario:
        if current_user.rol not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tu rol no tiene permisos para esta operación",
            )
        return current_user

    return checker


__all__ = ["get_current_user", "get_db", "require_roles"]
