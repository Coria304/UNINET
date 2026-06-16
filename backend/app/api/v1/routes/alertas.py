"""Endpoints de alertas de saturación (RF003)."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models import RolUsuario, Usuario
from app.schemas.alertas import AlertaAtenderIn, AlertaOut
from app.services.alertas import atender_alerta, listar_alertas

router = APIRouter(prefix="/alertas", tags=["alertas"])

_ROLES_ALERTAS = (RolUsuario.ADMINISTRADOR_TI, RolUsuario.PERSONAL_TECNICO)


@router.get(
    "",
    response_model=list[AlertaOut],
    summary="Lista de alertas de saturación (RF003)",
)
def get_alertas(
    solo_activas: bool = Query(default=True, description="Si True, solo devuelve alertas ACTIVAS"),
    limit: int = Query(default=50, ge=1, le=500, description="Máximo de resultados"),
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles(*_ROLES_ALERTAS)),
) -> list[AlertaOut]:
    return listar_alertas(db, solo_activas=solo_activas, limit=limit)


@router.patch(
    "/{alerta_id}/atender",
    response_model=AlertaOut,
    summary="Marcar una alerta como atendida (RF003)",
)
def atender(
    alerta_id: UUID,
    payload: AlertaAtenderIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles(*_ROLES_ALERTAS)),
) -> AlertaOut:
    return atender_alerta(
        db,
        alerta_id=alerta_id,
        usuario=current_user,
        comentario=payload.comentario_resolucion,
    )
