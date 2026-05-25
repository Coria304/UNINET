"""Tests del flujo de tickets (RF001 — reporte geolocalizado, RF004 — gestión).

Estilo BDD por criterio de aceptación. Cubre creación, validación de
ubicación, listado por rol, transiciones de estado y asignación.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.models import Aula, Edificio, EstadoTicket, Piso, RolUsuario, Usuario


def _token(client: TestClient, correo: str, password: str) -> str:
    resp = client.post("/api/v1/auth/login", json={"correo": correo, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# =====================================================================
# RF001 — El estudiante reporta una falla con ubicación geográfica.
# =====================================================================
def test_estudiante_crea_ticket_con_aula(
    client: TestClient, estudiante: Usuario, edificio: Edificio
) -> None:
    aula = edificio.pisos[0].aulas[0]
    token = _token(client, estudiante.correo, "Estudiante#2026")

    resp = client.post(
        "/api/v1/tickets",
        headers=_auth(token),
        json={
            "edificio_id": str(edificio.id),
            "aula_id": str(aula.id),
            "tipo_falla": "sin_senal",
            "descripcion": "No hay WiFi en T100.",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["estado"] == "activo"
    assert body["tipo_falla"] == "sin_senal"
    assert body["aula_id"] == str(aula.id)
    assert body["reportante"]["id"] == str(estudiante.id)
    assert body["asignado_a"] is None
    # Historial inicial registrado.
    assert len(body["historico"]) == 1
    assert body["historico"][0]["estado_nuevo"] == "activo"


def test_rechaza_aula_de_otro_edificio(
    client: TestClient, estudiante: Usuario, edificio: Edificio, db_session
) -> None:
    """El aula debe pertenecer al edificio reportado — caso clásico de error UX."""
    otro_edif = Edificio(codigo="ED-OTRO", nombre="Otro edificio")
    db_session.add(otro_edif)
    db_session.commit()
    aula_real = edificio.pisos[0].aulas[0]
    token = _token(client, estudiante.correo, "Estudiante#2026")

    resp = client.post(
        "/api/v1/tickets",
        headers=_auth(token),
        json={
            "edificio_id": str(otro_edif.id),
            "aula_id": str(aula_real.id),
            "tipo_falla": "lentitud",
        },
    )
    assert resp.status_code == 400
    assert "edificio" in resp.json()["detail"].lower()


def test_endpoint_ubicaciones_devuelve_arbol(
    client: TestClient, estudiante: Usuario, edificio: Edificio
) -> None:
    token = _token(client, estudiante.correo, "Estudiante#2026")
    resp = client.get("/api/v1/ubicaciones/edificios", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    e = data[0]
    assert e["codigo"] == "ED-TEST"
    assert len(e["pisos"]) == 1
    assert len(e["pisos"][0]["aulas"]) == 1
    assert e["pisos"][0]["aulas"][0]["codigo"] == "T100"


# =====================================================================
# RF004 — Visibilidad por rol.
# =====================================================================
def test_estudiante_solo_ve_sus_tickets(
    client: TestClient, estudiante: Usuario, edificio: Edificio, db_session
) -> None:
    # Segundo estudiante con su propio ticket.
    otra = Usuario(
        correo="otra@escom.ipn.mx",
        nombre_completo="Otra Alumna",
        password_hash=hash_password("Otra#2026"),
        rol=RolUsuario.ESTUDIANTE,
    )
    db_session.add(otra)
    db_session.commit()

    aula = edificio.pisos[0].aulas[0]
    t1 = _token(client, estudiante.correo, "Estudiante#2026")
    t2 = _token(client, otra.correo, "Otra#2026")

    # Cada uno crea uno.
    for token in (t1, t2):
        r = client.post(
            "/api/v1/tickets",
            headers=_auth(token),
            json={
                "edificio_id": str(edificio.id),
                "aula_id": str(aula.id),
                "tipo_falla": "lentitud",
            },
        )
        assert r.status_code == 201

    lista_1 = client.get("/api/v1/tickets", headers=_auth(t1)).json()
    lista_2 = client.get("/api/v1/tickets", headers=_auth(t2)).json()
    assert len(lista_1) == 1
    assert len(lista_2) == 1
    assert lista_1[0]["reportante_id"] == str(estudiante.id)
    assert lista_2[0]["reportante_id"] == str(otra.id)


def test_tecnico_ve_todos_los_tickets(
    client: TestClient,
    estudiante: Usuario,
    tecnico: Usuario,
    edificio: Edificio,
) -> None:
    aula = edificio.pisos[0].aulas[0]
    t_est = _token(client, estudiante.correo, "Estudiante#2026")
    client.post(
        "/api/v1/tickets",
        headers=_auth(t_est),
        json={
            "edificio_id": str(edificio.id),
            "aula_id": str(aula.id),
            "tipo_falla": "sin_senal",
        },
    )

    t_tec = _token(client, tecnico.correo, "Tecnico#2026")
    lista = client.get("/api/v1/tickets", headers=_auth(t_tec)).json()
    assert len(lista) == 1
    assert lista[0]["reportante_id"] == str(estudiante.id)


def test_estudiante_no_puede_ver_ticket_ajeno(
    client: TestClient,
    estudiante: Usuario,
    edificio: Edificio,
    db_session,
) -> None:
    aula = edificio.pisos[0].aulas[0]
    otra = Usuario(
        correo="ajena@escom.ipn.mx",
        nombre_completo="Ajena",
        password_hash=hash_password("Ajena#2026"),
        rol=RolUsuario.ESTUDIANTE,
    )
    db_session.add(otra)
    db_session.commit()

    t_otra = _token(client, otra.correo, "Ajena#2026")
    crear = client.post(
        "/api/v1/tickets",
        headers=_auth(t_otra),
        json={
            "edificio_id": str(edificio.id),
            "aula_id": str(aula.id),
            "tipo_falla": "otro",
        },
    ).json()

    t_est = _token(client, estudiante.correo, "Estudiante#2026")
    resp = client.get(f"/api/v1/tickets/{crear['id']}", headers=_auth(t_est))
    assert resp.status_code == 403


# =====================================================================
# RF004 — Transiciones de estado y asignación.
# =====================================================================
def test_tecnico_cambia_estado_y_registra_historial(
    client: TestClient,
    estudiante: Usuario,
    tecnico: Usuario,
    edificio: Edificio,
) -> None:
    aula = edificio.pisos[0].aulas[0]
    t_est = _token(client, estudiante.correo, "Estudiante#2026")
    ticket = client.post(
        "/api/v1/tickets",
        headers=_auth(t_est),
        json={
            "edificio_id": str(edificio.id),
            "aula_id": str(aula.id),
            "tipo_falla": "desconexion_intermitente",
        },
    ).json()

    t_tec = _token(client, tecnico.correo, "Tecnico#2026")

    # ACTIVO → EN_PROCESO, además asigno al técnico.
    r1 = client.patch(
        f"/api/v1/tickets/{ticket['id']}",
        headers=_auth(t_tec),
        json={
            "estado": "en_proceso",
            "asignado_a_id": str(tecnico.id),
            "comentario": "Voy a revisar el AP.",
        },
    )
    assert r1.status_code == 200, r1.text
    body = r1.json()
    assert body["estado"] == "en_proceso"
    assert body["asignado_a"]["id"] == str(tecnico.id)
    assert len(body["historico"]) == 2  # creación + transición
    transicion = body["historico"][1]
    assert transicion["estado_anterior"] == "activo"
    assert transicion["estado_nuevo"] == "en_proceso"
    assert transicion["comentario"] == "Voy a revisar el AP."

    # EN_PROCESO → RESUELTO cierra el ticket.
    r2 = client.patch(
        f"/api/v1/tickets/{ticket['id']}",
        headers=_auth(t_tec),
        json={"estado": "resuelto", "comentario": "AP reiniciado."},
    )
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["estado"] == "resuelto"
    assert body2["cerrado_at"] is not None


def test_no_se_puede_reabrir_un_ticket_resuelto(
    client: TestClient,
    estudiante: Usuario,
    tecnico: Usuario,
    edificio: Edificio,
) -> None:
    aula = edificio.pisos[0].aulas[0]
    t_est = _token(client, estudiante.correo, "Estudiante#2026")
    tk = client.post(
        "/api/v1/tickets",
        headers=_auth(t_est),
        json={
            "edificio_id": str(edificio.id),
            "aula_id": str(aula.id),
            "tipo_falla": "sin_senal",
        },
    ).json()

    t_tec = _token(client, tecnico.correo, "Tecnico#2026")
    client.patch(
        f"/api/v1/tickets/{tk['id']}", headers=_auth(t_tec), json={"estado": "resuelto"}
    )

    rebot = client.patch(
        f"/api/v1/tickets/{tk['id']}", headers=_auth(t_tec), json={"estado": "activo"}
    )
    assert rebot.status_code == 400
    assert "transicion" in rebot.json()["detail"].lower() or "puede" in rebot.json()["detail"].lower()


def test_estudiante_no_puede_actualizar_ticket(
    client: TestClient, estudiante: Usuario, edificio: Edificio
) -> None:
    aula = edificio.pisos[0].aulas[0]
    t_est = _token(client, estudiante.correo, "Estudiante#2026")
    tk = client.post(
        "/api/v1/tickets",
        headers=_auth(t_est),
        json={
            "edificio_id": str(edificio.id),
            "aula_id": str(aula.id),
            "tipo_falla": "otro",
        },
    ).json()

    resp = client.patch(
        f"/api/v1/tickets/{tk['id']}", headers=_auth(t_est), json={"estado": "en_proceso"}
    )
    assert resp.status_code == 403


def test_no_se_puede_asignar_a_un_estudiante(
    client: TestClient,
    estudiante: Usuario,
    tecnico: Usuario,
    edificio: Edificio,
) -> None:
    aula = edificio.pisos[0].aulas[0]
    t_est = _token(client, estudiante.correo, "Estudiante#2026")
    tk = client.post(
        "/api/v1/tickets",
        headers=_auth(t_est),
        json={
            "edificio_id": str(edificio.id),
            "aula_id": str(aula.id),
            "tipo_falla": "lentitud",
        },
    ).json()

    t_tec = _token(client, tecnico.correo, "Tecnico#2026")
    resp = client.patch(
        f"/api/v1/tickets/{tk['id']}",
        headers=_auth(t_tec),
        json={"asignado_a_id": str(estudiante.id)},
    )
    assert resp.status_code == 400
    assert "técnico" in resp.json()["detail"].lower() or "tecnico" in resp.json()["detail"].lower()


def test_filtro_por_estado_en_listado(
    client: TestClient,
    estudiante: Usuario,
    tecnico: Usuario,
    edificio: Edificio,
) -> None:
    aula = edificio.pisos[0].aulas[0]
    t_est = _token(client, estudiante.correo, "Estudiante#2026")
    # Tres tickets, dos los pasamos a en_proceso.
    ids = []
    for _ in range(3):
        tk = client.post(
            "/api/v1/tickets",
            headers=_auth(t_est),
            json={
                "edificio_id": str(edificio.id),
                "aula_id": str(aula.id),
                "tipo_falla": "lentitud",
            },
        ).json()
        ids.append(tk["id"])

    t_tec = _token(client, tecnico.correo, "Tecnico#2026")
    for tid in ids[:2]:
        client.patch(
            f"/api/v1/tickets/{tid}", headers=_auth(t_tec), json={"estado": "en_proceso"}
        )

    activos = client.get(
        "/api/v1/tickets", headers=_auth(t_tec), params={"estado": "activo"}
    ).json()
    en_proceso = client.get(
        "/api/v1/tickets", headers=_auth(t_tec), params={"estado": "en_proceso"}
    ).json()
    assert len(activos) == 1
    assert len(en_proceso) == 2
