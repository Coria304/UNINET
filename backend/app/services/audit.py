"""Servicio de auditoría (RNF010, LFPDPPP)."""

from __future__ import annotations

import ipaddress
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import AuditLog


def _normalize_ip(raw: str | None) -> str | None:
    """Devuelve la IP si es válida, o None en caso contrario.

    El TestClient de FastAPI envía 'testclient' como host, y detrás de
    proxies/CDNs pueden llegar otros valores no parseables. Mejor guardar
    NULL que romper el INSERT en la columna INET.
    """
    if not raw:
        return None
    try:
        ipaddress.ip_address(raw)
    except ValueError:
        return None
    return raw


def record_event(
    db: Session,
    *,
    accion: str,
    usuario_id: UUID | None = None,
    entidad: str | None = None,
    entidad_id: str | UUID | None = None,
    datos: dict[str, Any] | None = None,
    ip_origen: str | None = None,
) -> AuditLog:
    """Registra una acción crítica en el log de auditoría.

    Idempotente respecto a la transacción: añade y deja el flush a la
    sesión llamadora. Si se quiere persistir aunque la transacción
    principal falle, se debe pasar una sesión separada.
    """
    entry = AuditLog(
        usuario_id=usuario_id,
        accion=accion,
        entidad=entidad,
        entidad_id=str(entidad_id) if entidad_id is not None else None,
        datos=datos,
        ip_origen=_normalize_ip(ip_origen),
    )
    db.add(entry)
    return entry
