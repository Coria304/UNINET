"""Catálogo público de ubicaciones del campus (RF001)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models import Usuario
from app.repositories.ubicacion import EdificioRepository
from app.schemas.ubicacion import EdificioConPisos

router = APIRouter(prefix="/ubicaciones", tags=["ubicaciones"])


@router.get(
    "/edificios",
    response_model=list[EdificioConPisos],
    summary="Lista edificios con pisos y aulas",
)
def listar_edificios(
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> list:
    """Devuelve el árbol completo para alimentar el mapa del portal."""
    return EdificioRepository(db).list_full_tree()
