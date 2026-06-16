"""Endpoints de monitoreo en tiempo real (RF002)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models import AccessPoint, RolUsuario, Usuario
from app.schemas.monitoreo import MetricaIn, MonitoreoResponse
from app.services.alertas import evaluar_metricas_y_alertar
from app.services.monitoreo import obtener_estado_red, registrar_metrica

router = APIRouter(prefix="/monitoreo", tags=["monitoreo"])

_ROLES_MONITOREO = (RolUsuario.ADMINISTRADOR_TI, RolUsuario.PERSONAL_TECNICO)


@router.get(
    "/estado",
    response_model=MonitoreoResponse,
    summary="Estado actual de la red Wi-Fi (RF002)",
)
def estado_red(
    edificio_id: UUID | None = Query(
        default=None,
        description="Filtra APs por edificio. Si se omite, devuelve todos.",
    ),
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles(*_ROLES_MONITOREO)),
) -> MonitoreoResponse:
    return obtener_estado_red(db, edificio_id=edificio_id)


@router.post(
    "/metrica",
    status_code=status.HTTP_201_CREATED,
    summary="Ingesta de métrica de monitoreo (solo sistema de monitoreo)",
)
def ingresar_metrica(
    payload: MetricaIn,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles(RolUsuario.ADMINISTRADOR_TI)),
) -> dict:
    # Verificar que el AP existe
    ap = db.get(AccessPoint, payload.access_point_id)
    if ap is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Access point no encontrado",
        )

    metrica = registrar_metrica(
        db,
        access_point_id=payload.access_point_id,
        ancho_banda_mbps=payload.ancho_banda_mbps,
        latencia_ms=payload.latencia_ms,
        carga_pct=payload.carga_pct,
        paquetes_perdidos=payload.paquetes_perdidos,
        clientes_conectados=payload.clientes_conectados,
    )

    # Evaluar alertas automáticamente
    evaluar_metricas_y_alertar(db, metrica=metrica, access_point=ap)

    return {"status": "ok", "ts": metrica.ts.isoformat()}
