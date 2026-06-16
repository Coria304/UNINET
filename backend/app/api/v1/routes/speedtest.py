"""Endpoints de prueba de velocidad (RF008)."""

import os

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models import Usuario
from app.schemas.speedtest import SpeedtestResultadoIn, SpeedtestResultadoOut
from app.services import speedtest as svc

router = APIRouter(prefix="/speedtest", tags=["speedtest"])

_BLOB_MB_DEFAULT = 5
_BLOB_MB_MAX = 20


@router.get("/ping", summary="Latency probe — responde de inmediato")
def ping() -> dict:
    return {"pong": True}


@router.get("/blob", summary="Blob de prueba para medir velocidad de bajada")
def blob_download(
    size_mb: int = _BLOB_MB_DEFAULT,
    _: Usuario = Depends(get_current_user),
) -> Response:
    size_mb = min(max(size_mb, 1), _BLOB_MB_MAX)
    return Response(
        content=os.urandom(size_mb * 1024 * 1024),
        media_type="application/octet-stream",
        headers={"Cache-Control": "no-store"},
    )


@router.post("/blob", summary="Recibe blob de prueba para medir velocidad de subida")
async def blob_upload(
    request: Request,
    _: Usuario = Depends(get_current_user),
) -> dict:
    await request.body()  # consume y descarta
    return {"ok": True}


@router.post(
    "/resultado",
    response_model=SpeedtestResultadoOut,
    summary="Guarda el resultado de una prueba de velocidad",
    status_code=201,
)
def guardar_resultado(
    datos: SpeedtestResultadoIn,
    request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> SpeedtestResultadoOut:
    ip = request.client.host if request.client else None
    return svc.guardar_resultado(db, datos=datos, usuario=usuario, ip_origen=ip)


@router.get(
    "/historial",
    response_model=list[SpeedtestResultadoOut],
    summary="Historial de speedtests del usuario autenticado",
)
def historial(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> list[SpeedtestResultadoOut]:
    return svc.listar_historial(db, usuario=usuario)
