"""Dependencias compartidas para los endpoints FastAPI.

Las dependencias de autenticación (`get_current_user`, `require_role`) se
añadirán en Sprint 1 (RF009).
"""

from app.core.database import get_db

__all__ = ["get_db"]
