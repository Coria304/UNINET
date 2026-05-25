"""Fixtures pytest compartidos.

Cada test corre con esquema limpio: rollback al cierre de la sesión y
truncado de tablas entre tests. Redis se limpia con FLUSHDB para que los
retos MFA no contaminen casos posteriores.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.api.deps import get_db
from app.core.database import SessionLocal, engine
from app.core.redis import get_redis
from app.core.security import hash_password
from app.main import app
from app.models import Base, RolUsuario, Usuario


@pytest.fixture(scope="session", autouse=True)
def _prepare_schema() -> Generator[None, None, None]:
    """Crea las tablas necesarias en la BD de pruebas.

    En CI la BD ya viene migrada por Alembic. En desarrollo local
    Base.metadata.create_all es suficiente como red de seguridad.
    """
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(autouse=True)
def _clean_state() -> Generator[None, None, None]:
    """Vacía tablas y Redis antes de cada test."""
    with engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE audit_log, usuarios RESTART IDENTITY CASCADE"
            )
        )
    get_redis().flushdb()
    yield


@pytest.fixture
def db_session() -> Generator[Any, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Cliente FastAPI con la dependencia get_db real (mismo engine)."""

    def _override_get_db() -> Generator[Any, None, None]:
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# -------------------------------------------------------------------
# Fixtures de usuarios sembrados
# -------------------------------------------------------------------
@pytest.fixture
def estudiante(db_session) -> Usuario:
    user = Usuario(
        correo="alumna@escom.ipn.mx",
        nombre_completo="Alumna de Prueba",
        password_hash=hash_password("Estudiante#2026"),
        rol=RolUsuario.ESTUDIANTE,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin(db_session) -> Usuario:
    user = Usuario(
        correo="admin@escom.ipn.mx",
        nombre_completo="Admin de Prueba",
        password_hash=hash_password("Admin#2026"),
        rol=RolUsuario.ADMINISTRADOR_TI,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user
