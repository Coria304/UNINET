"""Endpoints de notificaciones del usuario actual (RF005)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models import Usuario
from app.repositories.notificacion import NotificacionRepository
from app.schemas.notificacion import NotificacionListResponse, NotificacionOut

router = APIRouter(prefix="/notificaciones", tags=["notificaciones"])


@router.get(
    "",
    response_model=NotificacionListResponse,
    summary="Lista notificaciones del usuario actual",
)
def listar(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    leida: bool | None = Query(default=None, description="Filtra por estado de lectura"),
    limit: int = Query(default=50, ge=1, le=200),
):
    repo = NotificacionRepository(db)
    items = repo.list_for_user(current_user.id, leida=leida, limit=limit)
    return NotificacionListResponse(
        items=[NotificacionOut.model_validate(n) for n in items],
        total_no_leidas=repo.count_unread(current_user.id),
    )


@router.post(
    "/{notificacion_id}/leer",
    response_model=NotificacionOut,
    summary="Marca una notificación como leída",
)
def marcar_leida(
    notificacion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> NotificacionOut:
    repo = NotificacionRepository(db)
    notif = repo.get(notificacion_id)
    if notif is None or notif.usuario_id != current_user.id:
        # No exponemos si existe o no para otro usuario.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada.",
        )
    repo.mark_read(notif)
    db.commit()
    db.refresh(notif)
    return NotificacionOut.model_validate(notif)


@router.post(
    "/leer-todas",
    summary="Marca como leídas todas las notificaciones del usuario",
)
def marcar_todas_leidas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    repo = NotificacionRepository(db)
    actualizadas = repo.mark_all_read(current_user.id)
    db.commit()
    return {"actualizadas": actualizadas}


@router.delete(
    "/{notificacion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Elimina una notificación del usuario actual",
)
def eliminar(
    notificacion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> None:
    repo = NotificacionRepository(db)
    notif = repo.get(notificacion_id)
    if notif is None or notif.usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada.",
        )
    repo.delete(notif)
    db.commit()
