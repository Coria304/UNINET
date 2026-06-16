"""Servicio de alertas de saturación (RF003).

Evalúa cada métrica entrante contra los umbrales configurados y genera
alertas cuando se supera algún umbral. Evita duplicados: no crea una
nueva alerta si ya existe una ACTIVA del mismo tipo para el mismo AP.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AccessPoint,
    Alerta,
    Aula,
    ConfiguracionUmbrales,
    Edificio,
    EstadoAlerta,
    MetricaMonitoreo,
    Piso,
    TipoAlerta,
    Usuario,
)
from app.schemas.alertas import AlertaOut

# Umbrales por defecto si no hay ConfiguracionUmbrales en BD.
_DEFAULT_UMBRAL_CARGA = 80.0
_DEFAULT_UMBRAL_LATENCIA = 200.0


def _get_umbrales(db: Session) -> tuple[float, float]:
    """Devuelve (umbral_carga_pct, umbral_latencia_ms)."""
    config = db.execute(select(ConfiguracionUmbrales).limit(1)).scalar_one_or_none()
    if config is None:
        return _DEFAULT_UMBRAL_CARGA, _DEFAULT_UMBRAL_LATENCIA
    return config.carga_pct, config.latencia_ms


def _alerta_activa_existe(
    db: Session, *, access_point_id: UUID, tipo: TipoAlerta
) -> bool:
    """Verifica si ya hay una alerta ACTIVA del tipo dado para este AP."""
    result = db.execute(
        select(Alerta.id).where(
            Alerta.access_point_id == access_point_id,
            Alerta.tipo == tipo,
            Alerta.estado == EstadoAlerta.ACTIVA,
        ).limit(1)
    ).scalar_one_or_none()
    return result is not None


def _row_to_alerta_out(row) -> AlertaOut:
    """Convierte una fila de consulta (con campos de AP y edificio) a AlertaOut."""
    return AlertaOut(
        id=row.id,
        access_point_id=row.access_point_id,
        ap_codigo=row.ap_codigo,
        ap_nombre=row.ap_nombre,
        edificio_codigo=row.edificio_codigo,
        tipo=row.tipo,
        estado=row.estado,
        umbral_violado=row.umbral_violado,
        valor_observado=row.valor_observado,
        detectada_at=row.detectada_at,
        atendida_at=row.atendida_at,
        comentario_resolucion=row.comentario_resolucion,
    )


def listar_alertas(
    db: Session,
    *,
    solo_activas: bool = True,
    limit: int = 50,
) -> list[AlertaOut]:
    """Lista alertas con información del AP y edificio asociado."""
    stmt = (
        select(
            Alerta.id,
            Alerta.access_point_id,
            AccessPoint.codigo.label("ap_codigo"),
            AccessPoint.nombre.label("ap_nombre"),
            Edificio.codigo.label("edificio_codigo"),
            Alerta.tipo,
            Alerta.estado,
            Alerta.umbral_violado,
            Alerta.valor_observado,
            Alerta.detectada_at,
            Alerta.atendida_at,
            Alerta.comentario_resolucion,
        )
        .join(AccessPoint, AccessPoint.id == Alerta.access_point_id)
        .outerjoin(Aula, Aula.id == AccessPoint.aula_id)
        .outerjoin(Piso, Piso.id == Aula.piso_id)
        .outerjoin(Edificio, Edificio.id == Piso.edificio_id)
        .order_by(Alerta.detectada_at.desc())
        .limit(limit)
    )
    if solo_activas:
        stmt = stmt.where(Alerta.estado == EstadoAlerta.ACTIVA)

    rows = db.execute(stmt).all()
    return [_row_to_alerta_out(r) for r in rows]


def atender_alerta(
    db: Session,
    *,
    alerta_id: UUID,
    usuario: Usuario,
    comentario: str | None,
) -> AlertaOut:
    """Marca una alerta como ATENDIDA y registra quién la resolvió."""
    from fastapi import HTTPException, status

    alerta = db.get(Alerta, alerta_id)
    if alerta is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerta no encontrada")

    alerta.estado = EstadoAlerta.ATENDIDA
    alerta.atendida_at = datetime.now(timezone.utc)
    alerta.atendida_por_id = usuario.id
    if comentario is not None:
        alerta.comentario_resolucion = comentario

    db.commit()
    db.refresh(alerta)

    # Traer datos del AP y edificio para el response
    row = db.execute(
        select(
            Alerta.id,
            Alerta.access_point_id,
            AccessPoint.codigo.label("ap_codigo"),
            AccessPoint.nombre.label("ap_nombre"),
            Edificio.codigo.label("edificio_codigo"),
            Alerta.tipo,
            Alerta.estado,
            Alerta.umbral_violado,
            Alerta.valor_observado,
            Alerta.detectada_at,
            Alerta.atendida_at,
            Alerta.comentario_resolucion,
        )
        .join(AccessPoint, AccessPoint.id == Alerta.access_point_id)
        .outerjoin(Aula, Aula.id == AccessPoint.aula_id)
        .outerjoin(Piso, Piso.id == Aula.piso_id)
        .outerjoin(Edificio, Edificio.id == Piso.edificio_id)
        .where(Alerta.id == alerta_id)
    ).one()

    return _row_to_alerta_out(row)


def evaluar_metricas_y_alertar(
    db: Session,
    *,
    metrica: MetricaMonitoreo,
    access_point: AccessPoint,
) -> list[Alerta]:
    """Evalúa la métrica recibida y crea alertas si se superan los umbrales.

    No crea alertas duplicadas: si ya existe una alerta ACTIVA del mismo
    tipo para el AP, se omite la creación.

    Returns:
        Lista de alertas nuevas creadas (puede ser vacía).
    """
    umbral_carga, umbral_latencia = _get_umbrales(db)
    nuevas: list[Alerta] = []
    now = datetime.now(timezone.utc)

    # --- Evaluación de carga ------------------------------------------
    if metrica.carga_pct > umbral_carga:
        if not _alerta_activa_existe(
            db,
            access_point_id=access_point.id,
            tipo=TipoAlerta.SATURACION_CARGA,
        ):
            alerta = Alerta(
                access_point_id=access_point.id,
                tipo=TipoAlerta.SATURACION_CARGA,
                estado=EstadoAlerta.ACTIVA,
                umbral_violado=umbral_carga,
                valor_observado=metrica.carga_pct,
                detectada_at=now,
            )
            db.add(alerta)
            nuevas.append(alerta)

    # --- Evaluación de latencia ---------------------------------------
    if metrica.latencia_ms > umbral_latencia:
        if not _alerta_activa_existe(
            db,
            access_point_id=access_point.id,
            tipo=TipoAlerta.LATENCIA_ALTA,
        ):
            alerta = Alerta(
                access_point_id=access_point.id,
                tipo=TipoAlerta.LATENCIA_ALTA,
                estado=EstadoAlerta.ACTIVA,
                umbral_violado=umbral_latencia,
                valor_observado=metrica.latencia_ms,
                detectada_at=now,
            )
            db.add(alerta)
            nuevas.append(alerta)

    if nuevas:
        db.commit()

    return nuevas
