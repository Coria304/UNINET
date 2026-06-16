from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import SpeedtestResultado, Usuario
from app.schemas.speedtest import SpeedtestResultadoIn


def guardar_resultado(
    db: Session,
    *,
    datos: SpeedtestResultadoIn,
    usuario: Usuario,
    ip_origen: str | None = None,
) -> SpeedtestResultado:
    resultado = SpeedtestResultado(
        usuario_id=usuario.id,
        edificio_id=datos.edificio_id,
        piso_id=datos.piso_id,
        aula_id=datos.aula_id,
        velocidad_bajada_mbps=datos.velocidad_bajada_mbps,
        velocidad_subida_mbps=datos.velocidad_subida_mbps,
        latencia_ms=datos.latencia_ms,
        ip_origen=ip_origen,
    )
    db.add(resultado)
    db.commit()
    db.refresh(resultado)
    return resultado


def listar_historial(
    db: Session,
    *,
    usuario: Usuario,
    limit: int = 20,
) -> list[SpeedtestResultado]:
    return list(
        db.execute(
            select(SpeedtestResultado)
            .where(SpeedtestResultado.usuario_id == usuario.id)
            .order_by(desc(SpeedtestResultado.ejecutado_at))
            .limit(limit)
        ).scalars()
    )
