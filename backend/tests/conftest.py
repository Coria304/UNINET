"""Fixtures pytest compartidos.

Cada test corre con esquema limpio: rollback al cierre de la sesión y
truncado de tablas entre tests. Redis se limpia con FLUSHDB para que los
retos MFA no contaminen casos posteriores.

Importante: los tests SIEMPRE corren contra la BD `uninet_test`, distinta
de `uninet` (la de desarrollo). El override de DATABASE_URL ocurre antes
de cualquier import de `app.*` para que `app.core.config` y el engine
de SQLAlchemy ya nazcan apuntando a la BD correcta. Si la BD de tests
no existe, se crea on-the-fly junto con las extensiones requeridas
(pgcrypto, citext, timescaledb).
"""

from __future__ import annotations

# --- Override de la BD ANTES de cualquier import de app.* -----------
import os
from collections.abc import Generator
from typing import Any
from urllib.parse import urlsplit

import psycopg

_TEST_DB_NAME = os.environ.get("UNINET_TEST_DB", "uninet_test")
_PG_USER = os.environ.get("POSTGRES_USER", "uninet")
_PG_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "uninet_dev")
_PG_HOST = "localhost"
_PG_PORT = os.environ.get("POSTGRES_PORT", "5432")

os.environ["DATABASE_URL"] = (
    f"postgresql+psycopg://{_PG_USER}:{_PG_PASSWORD}"
    f"@{_PG_HOST}:{_PG_PORT}/{_TEST_DB_NAME}"
)


def _ensure_test_database() -> None:
    """Crea la BD de tests si no existe y aplica las extensiones requeridas."""
    admin_dsn = (
        f"postgresql://{_PG_USER}:{_PG_PASSWORD}@{_PG_HOST}:{_PG_PORT}/postgres"
    )
    with psycopg.connect(admin_dsn, autocommit=True) as conn:
        cur = conn.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (_TEST_DB_NAME,)
        )
        if cur.fetchone() is None:
            # No se puede parametrizar DDL — el nombre viene de config, no de input externo.
            conn.execute(f'CREATE DATABASE "{_TEST_DB_NAME}"')

    test_dsn = (
        f"postgresql://{_PG_USER}:{_PG_PASSWORD}@{_PG_HOST}:{_PG_PORT}/{_TEST_DB_NAME}"
    )
    with psycopg.connect(test_dsn, autocommit=True) as conn:
        # Las extensiones replican lo que hace la migración 0001 — el create_all
        # de SQLAlchemy crea tablas pero no extensiones.
        conn.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
        conn.execute("CREATE EXTENSION IF NOT EXISTS citext")
        conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")


_ensure_test_database()
# Marker para debugging cuando alguien se confunde de BD.
assert urlsplit(os.environ["DATABASE_URL"]).path == f"/{_TEST_DB_NAME}", (
    "conftest no logró fijar la BD de tests — revisa el orden de imports."
)
# --------------------------------------------------------------------

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.api.deps import get_db
from app.core.database import SessionLocal, engine
from app.core.redis import get_redis
from app.core.security import hash_password
from app.main import app
from app.models import Aula, Base, Edificio, Piso, RolUsuario, Usuario


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
    """Vacía todas las tablas del schema y Redis antes de cada test.

    Descubre las tablas dinámicamente para que no haya que mantener una
    lista en sync conforme crece el modelo.
    """
    with engine.begin() as conn:
        tables = [
            row[0]
            for row in conn.execute(
                text(
                    "SELECT tablename FROM pg_tables "
                    "WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
                )
            )
        ]
        if tables:
            quoted = ", ".join(f'"{t}"' for t in tables)
            conn.execute(text(f"TRUNCATE {quoted} RESTART IDENTITY CASCADE"))
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


@pytest.fixture
def tecnico(db_session) -> Usuario:
    user = Usuario(
        correo="tecnico@escom.ipn.mx",
        nombre_completo="Técnico de Prueba",
        password_hash=hash_password("Tecnico#2026"),
        rol=RolUsuario.PERSONAL_TECNICO,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# -------------------------------------------------------------------
# Fixtures de ubicación (mínimo viable para tests de RF001/RF004)
# -------------------------------------------------------------------
@pytest.fixture
def edificio(db_session) -> Edificio:
    """Edificio con un piso y un aula listos para usar."""
    edif = Edificio(
        codigo="ED-TEST",
        nombre="Edificio de Pruebas",
        latitud=19.5046,
        longitud=-99.1467,
    )
    db_session.add(edif)
    db_session.flush()
    piso = Piso(edificio_id=edif.id, numero=1, nombre="Piso 1 (test)")
    db_session.add(piso)
    db_session.flush()
    aula = Aula(piso_id=piso.id, codigo="T100", nombre="Aula T100", tipo="aula")
    db_session.add(aula)
    db_session.commit()
    db_session.refresh(edif)
    return edif
