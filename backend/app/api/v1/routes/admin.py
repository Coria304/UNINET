"""Endpoints administrativos (Sprint 1: solo placeholder para validar RBAC)."""

from fastapi import APIRouter, Depends

from app.api.deps import require_roles
from app.models import RolUsuario, Usuario
from app.schemas.usuario import UsuarioOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/ping",
    response_model=UsuarioOut,
    summary="Verifica que el usuario tiene rol Administrador TI",
)
def admin_ping(
    current_user: Usuario = Depends(require_roles(RolUsuario.ADMINISTRADOR_TI)),
) -> Usuario:
    """Endpoint mínimo para validar CA-RF009-1 desde el cliente."""
    return current_user
