"""Tests del dashboard administrativo (RF007)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.models import Edificio, EstadoTicket, Ticket, Usuario


def _token(client: TestClient, correo: str, password: str) -> str:
    r = client.post(
        "/api/v1/auth/login", json={"correo": correo, "password": password}
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _token_admin(client: TestClient, correo: str, password: str) -> str:
    login = client.post(
        "/api/v1/auth/login", json={"correo": correo, "password": password}
    ).json()
    assert login.get("mfa_required") is True
    verify = client.post(
        "/api/v1/auth/mfa/verify",
        json={"challenge_id": login["challenge_id"], "code": login["dev_code"]},
    )
    assert verify.status_code == 200, verify.text
    return verify.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _crear_tickets_sembrados(
    db_session,
    reportante: Usuario,
    tecnico: Usuario,
    edificio: Edificio,
) -> dict[str, list[Ticket]]:
    """Crea 6 tickets representativos: 2 activos, 2 en_proceso, 2 resueltos."""
    aula = edificio.pisos[0].aulas[0]
    now = datetime.now(timezone.utc)
    out: dict[str, list[Ticket]] = {"activo": [], "en_proceso": [], "resuelto": []}

    for i in range(6):
        # tipos_falla varían para que el bucket de tipos tenga >1 elemento.
        tipo = ["sin_senal", "lentitud", "otro"][i % 3]
        t = Ticket(
            reportante_id=reportante.id,
            edificio_id=edificio.id,
            piso_id=aula.piso_id,
            aula_id=aula.id,
            tipo_falla=tipo,
            descripcion=f"Ticket sembrado #{i}",
        )
        if i < 2:
            t.estado = EstadoTicket.ACTIVO
            out["activo"].append(t)
        elif i < 4:
            t.estado = EstadoTicket.EN_PROCESO
            t.asignado_a_id = tecnico.id
            out["en_proceso"].append(t)
        else:
            t.estado = EstadoTicket.RESUELTO
            t.asignado_a_id = tecnico.id
            # Cerrado a las 2 y 4 horas → MTTR esperado = 3.0 horas
            t.cerrado_at = now + timedelta(hours=2 if i == 4 else 4)
            out["resuelto"].append(t)
        db_session.add(t)
    db_session.commit()
    # forzar refresh para que `created_at` esté seteado (server_default).
    for tickets in out.values():
        for t in tickets:
            db_session.refresh(t)
    return out


# =====================================================================
# Permisos: sólo ADMINISTRADOR_TI accede.
# =====================================================================
def test_estudiante_no_puede_ver_reportes(
    client: TestClient, estudiante: Usuario
) -> None:
    t = _token(client, estudiante.correo, "Estudiante#2026")
    r = client.get("/api/v1/reportes/resumen", headers=_auth(t))
    assert r.status_code == 403


def test_tecnico_no_puede_ver_reportes(
    client: TestClient, tecnico: Usuario
) -> None:
    t = _token(client, tecnico.correo, "Tecnico#2026")
    r = client.get("/api/v1/reportes/resumen", headers=_auth(t))
    assert r.status_code == 403


# =====================================================================
# Métricas: cuenta correctamente por estado y MTTR.
# =====================================================================
def test_resumen_cuenta_por_estado_y_mttr(
    client: TestClient,
    admin: Usuario,
    estudiante: Usuario,
    tecnico: Usuario,
    edificio: Edificio,
    db_session,
) -> None:
    _crear_tickets_sembrados(db_session, estudiante, tecnico, edificio)

    t = _token_admin(client, admin.correo, "Admin#2026")
    body = client.get("/api/v1/reportes/resumen", headers=_auth(t)).json()

    assert body["total"] == 6
    assert body["por_estado"]["activo"] == 2
    assert body["por_estado"]["en_proceso"] == 2
    assert body["por_estado"]["resuelto"] == 2
    # 2 cerrados a las 2h y a las 4h → promedio 3h
    assert body["mttr_horas"] == 3.0
    # Sin asignar: los 2 activos (los en_proceso ya tienen tecnico).
    assert body["sin_asignar"] == 2


def test_top_edificios_y_tipos(
    client: TestClient,
    admin: Usuario,
    estudiante: Usuario,
    tecnico: Usuario,
    edificio: Edificio,
    db_session,
) -> None:
    _crear_tickets_sembrados(db_session, estudiante, tecnico, edificio)

    t = _token_admin(client, admin.correo, "Admin#2026")
    body = client.get("/api/v1/reportes/resumen", headers=_auth(t)).json()

    # Solo hay 1 edificio sembrado, debería aparecer con total=6.
    assert len(body["top_edificios"]) == 1
    assert body["top_edificios"][0]["codigo"] == "ED-TEST"
    assert body["top_edificios"][0]["total"] == 6

    # Los 6 tickets se repartieron entre 3 tipos (sin_senal, lentitud, otro).
    tipos = {b["tipo"]: b["total"] for b in body["top_tipos"]}
    assert sum(tipos.values()) == 6
    assert set(tipos.keys()) == {"sin_senal", "lentitud", "otro"}


def test_filtro_por_fechas_excluye_tickets_fuera_de_rango(
    client: TestClient,
    admin: Usuario,
    estudiante: Usuario,
    tecnico: Usuario,
    edificio: Edificio,
    db_session,
) -> None:
    _crear_tickets_sembrados(db_session, estudiante, tecnico, edificio)

    t = _token_admin(client, admin.correo, "Admin#2026")
    # Rango muy en el pasado: no debería haber nada.
    desde = (datetime.now(timezone.utc) - timedelta(days=365)).isoformat()
    hasta = (datetime.now(timezone.utc) - timedelta(days=364)).isoformat()
    body = client.get(
        "/api/v1/reportes/resumen",
        headers=_auth(t),
        params={"desde": desde, "hasta": hasta},
    ).json()
    assert body["total"] == 0
    assert body["mttr_horas"] is None


def test_granularidad_valida_o_default(
    client: TestClient,
    admin: Usuario,
    estudiante: Usuario,
    tecnico: Usuario,
    edificio: Edificio,
    db_session,
) -> None:
    _crear_tickets_sembrados(db_session, estudiante, tecnico, edificio)
    t = _token_admin(client, admin.correo, "Admin#2026")

    # Granularidad válida
    body = client.get(
        "/api/v1/reportes/resumen",
        headers=_auth(t),
        params={"granularidad": "week"},
    ).json()
    assert body["granularidad"] == "week"

    # Granularidad inválida → 422 (pattern de Query la rechaza)
    bad = client.get(
        "/api/v1/reportes/resumen",
        headers=_auth(t),
        params={"granularidad": "anual"},
    )
    assert bad.status_code == 422


def test_resumen_vacio_no_falla(
    client: TestClient, admin: Usuario
) -> None:
    """Sin tickets en la BD el endpoint sigue respondiendo (todos en cero)."""
    t = _token_admin(client, admin.correo, "Admin#2026")
    body = client.get("/api/v1/reportes/resumen", headers=_auth(t)).json()

    assert body["total"] == 0
    assert body["mttr_horas"] is None
    assert body["top_edificios"] == []
    assert body["top_tipos"] == []
    assert body["serie_temporal"] == []
