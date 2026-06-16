"""Endpoints de reportes agregados (RF007).

Sólo accesibles al rol ADMINISTRADOR_TI: contienen métricas operacionales
(MTTR, top edificios) que no se exponen al público.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models import RolUsuario, Usuario
from app.schemas.reportes import MapaCalorResponse, ResumenReporte
from app.services.reportes import generar_mapa_calor, generar_resumen

router = APIRouter(prefix="/reportes", tags=["reportes"])


@router.get(
    "/resumen",
    response_model=ResumenReporte,
    summary="Resumen agregado de tickets para el dashboard administrativo",
)
def resumen(
    desde: datetime | None = Query(
        default=None,
        description="ISO 8601. Default: hace 30 días.",
    ),
    hasta: datetime | None = Query(
        default=None,
        description="ISO 8601. Default: ahora.",
    ),
    granularidad: str = Query(
        default="day",
        pattern="^(day|week|month)$",
        description="Granularidad de la serie temporal.",
    ),
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles(RolUsuario.ADMINISTRADOR_TI)),
) -> ResumenReporte:
    return generar_resumen(
        db, desde=desde, hasta=hasta, granularidad=granularidad
    )


@router.get(
    "/mapa-calor",
    response_model=MapaCalorResponse,
    summary="Densidad de tickets por edificio para heatmap (RF003)",
)
def mapa_calor(
    desde: datetime | None = Query(default=None, description="ISO 8601. Default: hace 30 días."),
    hasta: datetime | None = Query(default=None, description="ISO 8601. Default: ahora."),
    db: Session = Depends(get_db),
    _: Usuario = Depends(
        require_roles(RolUsuario.ADMINISTRADOR_TI, RolUsuario.PERSONAL_TECNICO)
    ),
) -> MapaCalorResponse:
    return generar_mapa_calor(db, desde=desde, hasta=hasta)
