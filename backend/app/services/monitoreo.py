"""Servicio de monitoreo en tiempo real (RF002).

Calcula el estado de la red a partir de la última métrica registrada
por cada access point activo. El semáforo de estado clasifica la carga
según umbrales fijos: saturated > 80 % carga o > 200 ms latencia,
high > 60 % o > 100 ms, good para el resto.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AccessPoint,
    Alerta,
    Aula,
    Edificio,
    EstadoAlerta,
    MetricaMonitoreo,
    Piso,
)
from app.schemas.monitoreo import AccessPointEstado, MetricaResumen, MonitoreoResponse


def _semaforo(carga_pct: float, latencia_ms: float) -> str:
    if carga_pct > 80 or latencia_ms > 200:
        return "saturated"
    if carga_pct > 60 or latencia_ms > 100:
        return "high"
    return "good"


def obtener_estado_red(
    db: Session,
    *,
    edificio_id: UUID | None = None,
) -> MonitoreoResponse:
    """Devuelve el estado actual de todos los APs activos.

    Args:
        db: Sesión de SQLAlchemy.
        edificio_id: Si se especifica, filtra APs que pertenezcan a ese edificio.
    """
    # --- Consulta base de APs activos con su jerarquía ----------------
    stmt_aps = (
        select(
            AccessPoint.id,
            AccessPoint.codigo,
            AccessPoint.nombre,
            AccessPoint.banda,
            AccessPoint.activo,
            Edificio.id.label("edificio_id"),
            Edificio.codigo.label("edificio_codigo"),
            Piso.id.label("piso_id"),
            # Coordenadas del edificio como proxy del AP
            Edificio.latitud.label("latitud"),
            Edificio.longitud.label("longitud"),
        )
        .outerjoin(Aula, Aula.id == AccessPoint.aula_id)
        .outerjoin(Piso, Piso.id == Aula.piso_id)
        .outerjoin(Edificio, Edificio.id == Piso.edificio_id)
        .where(AccessPoint.activo.is_(True))
    )

    if edificio_id is not None:
        stmt_aps = stmt_aps.where(Edificio.id == edificio_id)

    ap_rows = db.execute(stmt_aps).all()

    if not ap_rows:
        return MonitoreoResponse(total=0, activos=0, con_alertas=0, access_points=[])

    ap_ids = [r.id for r in ap_rows]

    # --- Última métrica por AP (subquery con MAX(ts)) ------------------
    sub_max_ts = (
        select(
            MetricaMonitoreo.access_point_id,
            func.max(MetricaMonitoreo.ts).label("max_ts"),
        )
        .where(MetricaMonitoreo.access_point_id.in_(ap_ids))
        .group_by(MetricaMonitoreo.access_point_id)
        .subquery()
    )

    stmt_metricas = select(MetricaMonitoreo).join(
        sub_max_ts,
        (MetricaMonitoreo.access_point_id == sub_max_ts.c.access_point_id)
        & (MetricaMonitoreo.ts == sub_max_ts.c.max_ts),
    )
    metrica_rows = db.execute(stmt_metricas).scalars().all()
    metricas_by_ap: dict[UUID, MetricaMonitoreo] = {m.access_point_id: m for m in metrica_rows}

    # --- APs con alertas activas --------------------------------------
    alertas_activas_ids: set[UUID] = set(
        db.execute(
            select(Alerta.access_point_id)
            .where(
                Alerta.access_point_id.in_(ap_ids),
                Alerta.estado == EstadoAlerta.ACTIVA,
            )
            .distinct()
        ).scalars()
    )

    # --- Construir respuesta -------------------------------------------
    estados: list[AccessPointEstado] = []
    for row in ap_rows:
        metrica = metricas_by_ap.get(row.id)
        metrica_resumen: MetricaResumen | None = None
        if metrica is not None:
            metrica_resumen = MetricaResumen(
                ts=metrica.ts,
                ancho_banda_mbps=metrica.ancho_banda_mbps,
                latencia_ms=metrica.latencia_ms,
                carga_pct=metrica.carga_pct,
                clientes_conectados=metrica.clientes_conectados,
                estado_semaforo=_semaforo(metrica.carga_pct, metrica.latencia_ms),
            )

        estados.append(
            AccessPointEstado(
                id=row.id,
                codigo=row.codigo,
                nombre=row.nombre,
                edificio_id=row.edificio_id,
                edificio_codigo=row.edificio_codigo,
                piso_id=row.piso_id,
                latitud=row.latitud,
                longitud=row.longitud,
                activo=row.activo,
                banda=row.banda,
                ultima_metrica=metrica_resumen,
            )
        )

    total = len(estados)
    activos = sum(1 for e in estados if e.activo)
    con_alertas = sum(1 for row in ap_rows if row.id in alertas_activas_ids)

    return MonitoreoResponse(
        total=total,
        activos=activos,
        con_alertas=con_alertas,
        access_points=estados,
    )


def registrar_metrica(
    db: Session,
    *,
    access_point_id: UUID,
    ancho_banda_mbps: float,
    latencia_ms: float,
    carga_pct: float,
    paquetes_perdidos: int,
    clientes_conectados: int,
) -> MetricaMonitoreo:
    """Persiste una nueva métrica de monitoreo."""
    metrica = MetricaMonitoreo(
        ts=datetime.now(timezone.utc),
        access_point_id=access_point_id,
        ancho_banda_mbps=ancho_banda_mbps,
        latencia_ms=latencia_ms,
        carga_pct=carga_pct,
        paquetes_perdidos=paquetes_perdidos,
        clientes_conectados=clientes_conectados,
    )
    db.add(metrica)
    db.commit()
    db.refresh(metrica)
    return metrica
