"""Tests del endpoint de mapa de calor (RF003)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.models import (
    Aula,
    Edificio,
    EstadoTicket,
    Piso,
    Ticket,
    Usuario,
)


def _token(client: TestClient, correo: str, password: str) -> str:
    r = client.post(
        "/api/v1/auth/login", json={"correo": correo, "password": password}
    )
    assert r.status_code == 200
    return r.json()["access_token"]


def _token_admin(client: TestClient, correo: str, password: str) -> str:
    login = client.post(
        "/api/v1/auth/login", json={"correo": correo, "password": password}
    ).json()
    verify = client.post(
        "/api/v1/auth/mfa/verify",
        json={"challenge_id": login["challenge_id"], "code": login["dev_code"]},
    )
    return verify.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_estudiante_no_puede_ver_mapa_calor(
    client: TestClient, estudiante: Usuario
) -> None:
    t = _token(client, estudiante.correo, "Estudiante#2026")
    r = client.get("/api/v1/reportes/mapa-calor", headers=_auth(t))
    assert r.status_code == 403


def test_tecnico_si_puede_ver_mapa_calor(
    client: TestClient, tecnico: Usuario
) -> None:
    """A diferencia del resumen SLA, el mapa lo necesita el técnico para
    saber adónde ir."""
    t = _token(client, tecnico.correo, "Tecnico#2026")
    r = client.get("/api/v1/reportes/mapa-calor", headers=_auth(t))
    assert r.status_code == 200


def test_agrupa_tickets_por_edificio(
    client: TestClient,
    estudiante: Usuario,
    admin: Usuario,
    edificio: Edificio,
    db_session,
) -> None:
    # 3 tickets en el edificio sembrado (que ya tiene lat/lon).
    aula = edificio.pisos[0].aulas[0]
    for _ in range(3):
        db_session.add(
            Ticket(
                reportante_id=estudiante.id,
                edificio_id=edificio.id,
                piso_id=aula.piso_id,
                aula_id=aula.id,
                tipo_falla="sin_senal",
                estado=EstadoTicket.ACTIVO,
            )
        )
    db_session.commit()

    t = _token_admin(client, admin.correo, "Admin#2026")
    body = client.get("/api/v1/reportes/mapa-calor", headers=_auth(t)).json()

    assert body["total"] == 3
    assert len(body["puntos"]) == 1
    p = body["puntos"][0]
    assert p["codigo"] == "ED-TEST"
    assert p["total"] == 3
    assert p["latitud"] == 19.5046
    assert p["longitud"] == -99.1467


def test_edificio_sin_coordenadas_no_aparece(
    client: TestClient,
    estudiante: Usuario,
    admin: Usuario,
    edificio: Edificio,
    db_session,
) -> None:
    """Un edificio sin lat/lon no se puede dibujar; debe omitirse."""
    sin_coords = Edificio(codigo="ED-NULL", nombre="Sin coords")
    db_session.add(sin_coords)
    db_session.flush()
    piso = Piso(edificio_id=sin_coords.id, numero=0, nombre="PB")
    db_session.add(piso)
    db_session.flush()
    aula = Aula(piso_id=piso.id, codigo="X01")
    db_session.add(aula)
    db_session.commit()

    db_session.add(
        Ticket(
            reportante_id=estudiante.id,
            edificio_id=sin_coords.id,
            piso_id=piso.id,
            aula_id=aula.id,
            tipo_falla="otro",
            estado=EstadoTicket.ACTIVO,
        )
    )
    # Y uno en el edificio con coords para tener algo en el payload.
    aula_real = edificio.pisos[0].aulas[0]
    db_session.add(
        Ticket(
            reportante_id=estudiante.id,
            edificio_id=edificio.id,
            piso_id=aula_real.piso_id,
            aula_id=aula_real.id,
            tipo_falla="otro",
            estado=EstadoTicket.ACTIVO,
        )
    )
    db_session.commit()

    t = _token_admin(client, admin.correo, "Admin#2026")
    body = client.get("/api/v1/reportes/mapa-calor", headers=_auth(t)).json()

    codigos = {p["codigo"] for p in body["puntos"]}
    assert "ED-TEST" in codigos
    assert "ED-NULL" not in codigos
    # `total` cuenta solo lo dibujable.
    assert body["total"] == 1


def test_filtro_de_fechas_aplica(
    client: TestClient,
    estudiante: Usuario,
    admin: Usuario,
    edificio: Edificio,
    db_session,
) -> None:
    aula = edificio.pisos[0].aulas[0]
    db_session.add(
        Ticket(
            reportante_id=estudiante.id,
            edificio_id=edificio.id,
            piso_id=aula.piso_id,
            aula_id=aula.id,
            tipo_falla="sin_senal",
            estado=EstadoTicket.ACTIVO,
        )
    )
    db_session.commit()

    t = _token_admin(client, admin.correo, "Admin#2026")
    desde = (datetime.now(timezone.utc) - timedelta(days=365)).isoformat()
    hasta = (datetime.now(timezone.utc) - timedelta(days=364)).isoformat()
    body = client.get(
        "/api/v1/reportes/mapa-calor",
        headers=_auth(t),
        params={"desde": desde, "hasta": hasta},
    ).json()
    assert body["total"] == 0
    assert body["puntos"] == []
