"""Agregaciones para el dashboard administrativo (RF007).

Una sola función pública (`generar_resumen`) responde el panel completo.
Hace ~6 queries cortas y las une en un payload del tamaño justo para
una sola pantalla. Cuando el panel crezca se puede partir en endpoints
independientes sin tocar el frontend gracias al schema versionado.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models import Edificio, EstadoTicket, Ticket
from app.schemas.reportes import (
    BucketEdificio,
    BucketTipoFalla,
    ContadorPorEstado,
    MapaCalorResponse,
    PuntoMapaCalor,
    PuntoSerieTemporal,
    ResumenReporte,
)

# Granularidades soportadas para series temporales — todas válidas para
# `date_trunc` de Postgres.
_GRANULARIDADES_VALIDAS = frozenset({"day", "week", "month"})


def _normalizar_rango(
    desde: datetime | None, hasta: datetime | None
) -> tuple[datetime, datetime]:
    """Default: últimos 30 días, todo en UTC y aware."""
    if hasta is None:
        hasta = datetime.now(timezone.utc)
    if desde is None:
        desde = hasta - timedelta(days=30)
    # Forzar tz-aware (asume UTC si se reciben naive).
    if desde.tzinfo is None:
        desde = desde.replace(tzinfo=timezone.utc)
    if hasta.tzinfo is None:
        hasta = hasta.replace(tzinfo=timezone.utc)
    return desde, hasta


def generar_resumen(
    db: Session,
    *,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    granularidad: str = "day",
    top_n: int = 5,
) -> ResumenReporte:
    """Calcula el snapshot del rango dado. Todas las queries filtran por
    `Ticket.created_at` para que el rango sea coherente entre métricas."""
    if granularidad not in _GRANULARIDADES_VALIDAS:
        granularidad = "day"

    desde, hasta = _normalizar_rango(desde, hasta)
    base_filter = (Ticket.created_at >= desde, Ticket.created_at <= hasta)

    # --- Conteo por estado (1 query con CASE) ---------------------------
    estado_counts = db.execute(
        select(
            Ticket.estado,
            func.count(Ticket.id),
        )
        .where(*base_filter)
        .group_by(Ticket.estado)
    ).all()
    por_estado_dict = {row[0]: row[1] for row in estado_counts}
    por_estado = ContadorPorEstado(
        activo=por_estado_dict.get(EstadoTicket.ACTIVO, 0),
        en_proceso=por_estado_dict.get(EstadoTicket.EN_PROCESO, 0),
        resuelto=por_estado_dict.get(EstadoTicket.RESUELTO, 0),
    )
    total = sum(por_estado_dict.values())

    # --- MTTR (mean time to resolve) ------------------------------------
    # AVG sobre tickets resueltos del rango. Postgres devuelve el diff
    # como interval, lo convertimos a horas con EXTRACT(EPOCH).
    mttr_segundos = db.scalar(
        select(
            func.avg(
                func.extract("epoch", Ticket.cerrado_at - Ticket.created_at)
            )
        ).where(
            *base_filter,
            Ticket.estado == EstadoTicket.RESUELTO,
            Ticket.cerrado_at.isnot(None),
        )
    )
    mttr_horas = (
        round(float(mttr_segundos) / 3600.0, 2) if mttr_segundos is not None else None
    )

    # --- Sin asignar (no resueltos sin técnico) -------------------------
    sin_asignar = (
        db.scalar(
            select(func.count(Ticket.id)).where(
                *base_filter,
                Ticket.asignado_a_id.is_(None),
                Ticket.estado != EstadoTicket.RESUELTO,
            )
        )
        or 0
    )

    # --- Top edificios --------------------------------------------------
    rows_edif = db.execute(
        select(
            Edificio.id,
            Edificio.codigo,
            Edificio.nombre,
            func.count(Ticket.id).label("total"),
        )
        .join(Ticket, Ticket.edificio_id == Edificio.id)
        .where(*base_filter)
        .group_by(Edificio.id, Edificio.codigo, Edificio.nombre)
        .order_by(desc("total"))
        .limit(top_n)
    ).all()
    top_edificios = [
        BucketEdificio(
            edificio_id=r[0], codigo=r[1], nombre=r[2], total=r[3]
        )
        for r in rows_edif
    ]

    # --- Top tipos de falla ---------------------------------------------
    rows_tipo = db.execute(
        select(Ticket.tipo_falla, func.count(Ticket.id).label("total"))
        .where(*base_filter)
        .group_by(Ticket.tipo_falla)
        .order_by(desc("total"))
    ).all()
    top_tipos = [BucketTipoFalla(tipo=r[0], total=r[1]) for r in rows_tipo]

    # --- Serie temporal -------------------------------------------------
    bucket = func.date_trunc(granularidad, Ticket.created_at)
    rows_serie = db.execute(
        select(bucket.label("fecha"), func.count(Ticket.id).label("total"))
        .where(*base_filter)
        .group_by("fecha")
        .order_by("fecha")
    ).all()
    serie_temporal = [
        PuntoSerieTemporal(fecha=r[0], total=r[1]) for r in rows_serie
    ]

    return ResumenReporte(
        desde=desde,
        hasta=hasta,
        total=total,
        por_estado=por_estado,
        mttr_horas=mttr_horas,
        sin_asignar=sin_asignar,
        top_edificios=top_edificios,
        top_tipos=top_tipos,
        serie_temporal=serie_temporal,
        granularidad=granularidad,
    )


def generar_mapa_calor(
    db: Session,
    *,
    desde: datetime | None = None,
    hasta: datetime | None = None,
) -> MapaCalorResponse:
    """Densidad de tickets por edificio para el heatmap (RF003).

    Devuelve solo edificios con coordenadas geográficas — un edificio sin
    lat/lon no puede dibujarse en el mapa, así que lo omitimos. El campo
    `total` se usa como "peso" para la intensidad del calor.
    """
    desde, hasta = _normalizar_rango(desde, hasta)

    rows = db.execute(
        select(
            Edificio.id,
            Edificio.codigo,
            Edificio.nombre,
            Edificio.latitud,
            Edificio.longitud,
            func.count(Ticket.id).label("total"),
        )
        .join(Ticket, Ticket.edificio_id == Edificio.id)
        .where(
            Ticket.created_at >= desde,
            Ticket.created_at <= hasta,
            Edificio.latitud.isnot(None),
            Edificio.longitud.isnot(None),
        )
        .group_by(
            Edificio.id, Edificio.codigo, Edificio.nombre, Edificio.latitud, Edificio.longitud
        )
        .order_by(desc("total"))
    ).all()

    puntos = [
        PuntoMapaCalor(
            edificio_id=r[0],
            codigo=r[1],
            nombre=r[2],
            latitud=float(r[3]),
            longitud=float(r[4]),
            total=r[5],
        )
        for r in rows
    ]

    return MapaCalorResponse(
        desde=desde,
        hasta=hasta,
        puntos=puntos,
        total=sum(p.total for p in puntos),
    )
