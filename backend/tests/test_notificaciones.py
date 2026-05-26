"""Tests del flujo de notificaciones (RF005).

Verifica la entrega in-app cuando se crean y actualizan tickets, los
endpoints de listado/marcado y la tolerancia ante SMTP no configurado.
"""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.models import Edificio, RolUsuario, Usuario


def _token(client: TestClient, correo: str, password: str) -> str:
    """Login normal. Para usuarios admin con MFA usar `_token_admin`."""
    resp = client.post(
        "/api/v1/auth/login", json={"correo": correo, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _token_admin(client: TestClient, correo: str, password: str) -> str:
    """Login + verify MFA en un solo paso usando `dev_code` (entorno dev)."""
    login = client.post(
        "/api/v1/auth/login", json={"correo": correo, "password": password}
    ).json()
    assert login.get("mfa_required") is True, login
    verify = client.post(
        "/api/v1/auth/mfa/verify",
        json={"challenge_id": login["challenge_id"], "code": login["dev_code"]},
    )
    assert verify.status_code == 200, verify.text
    return verify.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# =====================================================================
# RF005 — Operadores se enteran de nuevos reportes.
# =====================================================================
def test_crear_ticket_notifica_a_todos_los_operadores(
    client: TestClient,
    estudiante: Usuario,
    tecnico: Usuario,
    admin: Usuario,
    edificio: Edificio,
    db_session,
) -> None:
    # Un operador extra inactivo NO debería recibir notificaciones.
    tecnico_inactivo = Usuario(
        correo="tecnico_off@escom.ipn.mx",
        nombre_completo="Técnico Inactivo",
        password_hash=hash_password("Tecnico#2026"),
        rol=RolUsuario.PERSONAL_TECNICO,
        activo=False,
    )
    db_session.add(tecnico_inactivo)
    db_session.commit()

    aula = edificio.pisos[0].aulas[0]
    t_est = _token(client, estudiante.correo, "Estudiante#2026")
    resp = client.post(
        "/api/v1/tickets",
        headers=_auth(t_est),
        json={
            "edificio_id": str(edificio.id),
            "aula_id": str(aula.id),
            "tipo_falla": "sin_senal",
            "descripcion": "Sin WiFi en T100.",
        },
    )
    assert resp.status_code == 201, resp.text

    # Técnico activo recibe notificación.
    t_tec = _token(client, tecnico.correo, "Tecnico#2026")
    notifs_tec = client.get("/api/v1/notificaciones", headers=_auth(t_tec)).json()
    assert notifs_tec["total_no_leidas"] == 1
    assert notifs_tec["items"][0]["tipo"] == "ticket_creado"
    assert notifs_tec["items"][0]["entidad_tipo"] == "ticket"

    # Admin TI también (requiere MFA).
    t_adm = _token_admin(client, admin.correo, "Admin#2026")
    notifs_adm = client.get("/api/v1/notificaciones", headers=_auth(t_adm)).json()
    assert notifs_adm["total_no_leidas"] == 1

    # Técnico inactivo NO debe haber recibido nada.
    notif_inactivo = (
        db_session.execute(
            __import__("sqlalchemy").text(
                "SELECT count(*) FROM notificaciones WHERE usuario_id = :uid"
            ),
            {"uid": str(tecnico_inactivo.id)},
        ).scalar()
        or 0
    )
    assert notif_inactivo == 0


# =====================================================================
# RF005 — El reportante se entera de cambios de estado.
# =====================================================================
def test_cambio_de_estado_notifica_al_reportante(
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
    client.patch(
        f"/api/v1/tickets/{tk['id']}",
        headers=_auth(t_tec),
        json={"estado": "en_proceso", "comentario": "Voy en camino."},
    )

    # El estudiante debería ver UNA notificación de cambio de estado.
    notifs_est = client.get("/api/v1/notificaciones", headers=_auth(t_est)).json()
    items = [n for n in notifs_est["items"] if n["tipo"] == "ticket_estado_cambio"]
    assert len(items) == 1
    assert "en_proceso" in items[0]["titulo"] or "en proceso" in items[0]["titulo"]
    # El comentario debe aparecer en el cuerpo.
    assert "Voy en camino" in items[0]["mensaje"]


# =====================================================================
# RF005 — Un técnico asignado por otro operador recibe notificación.
# =====================================================================
def test_asignacion_a_otro_tecnico_dispara_notificacion(
    client: TestClient,
    estudiante: Usuario,
    tecnico: Usuario,
    admin: Usuario,
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
            "tipo_falla": "otro",
        },
    ).json()

    # Admin se loguea (con MFA) y asigna el ticket al técnico.
    t_adm = _token_admin(client, admin.correo, "Admin#2026")
    client.patch(
        f"/api/v1/tickets/{tk['id']}",
        headers=_auth(t_adm),
        json={"asignado_a_id": str(tecnico.id)},
    )

    t_tec = _token(client, tecnico.correo, "Tecnico#2026")
    notifs = client.get("/api/v1/notificaciones", headers=_auth(t_tec)).json()
    tipos = {n["tipo"] for n in notifs["items"]}
    assert "ticket_asignado" in tipos


def test_tecnico_asignandose_a_si_mismo_no_se_notifica(
    client: TestClient,
    estudiante: Usuario,
    tecnico: Usuario,
    edificio: Edificio,
) -> None:
    """Auto-asignación no genera notificación redundante."""
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

    t_tec = _token(client, tecnico.correo, "Tecnico#2026")
    client.patch(
        f"/api/v1/tickets/{tk['id']}",
        headers=_auth(t_tec),
        json={"asignado_a_id": str(tecnico.id)},
    )

    notifs = client.get("/api/v1/notificaciones", headers=_auth(t_tec)).json()
    # Sólo tiene la de TICKET_CREADO (porque es operador), no debería haber
    # una TICKET_ASIGNADO porque se asignó a sí mismo.
    tipos = [n["tipo"] for n in notifs["items"]]
    assert tipos.count("ticket_asignado") == 0


# =====================================================================
# Endpoints: filtros, marcar leída, leer-todas.
# =====================================================================
def test_marcar_leida_y_filtro_por_leida(
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
    # Cambio para generar notif al estudiante.
    client.patch(
        f"/api/v1/tickets/{tk['id']}",
        headers=_auth(t_tec),
        json={"estado": "en_proceso"},
    )

    notifs = client.get("/api/v1/notificaciones", headers=_auth(t_est)).json()
    assert notifs["total_no_leidas"] == 1
    nid = notifs["items"][0]["id"]

    leida = client.post(
        f"/api/v1/notificaciones/{nid}/leer", headers=_auth(t_est)
    ).json()
    assert leida["leida"] is True
    assert leida["leida_at"] is not None

    # Filtro leida=false ahora devuelve 0.
    sin_leer = client.get(
        "/api/v1/notificaciones", headers=_auth(t_est), params={"leida": "false"}
    ).json()
    assert len(sin_leer["items"]) == 0
    assert sin_leer["total_no_leidas"] == 0


def test_marcar_todas_leidas(
    client: TestClient,
    estudiante: Usuario,
    tecnico: Usuario,
    edificio: Edificio,
) -> None:
    aula = edificio.pisos[0].aulas[0]
    t_est = _token(client, estudiante.correo, "Estudiante#2026")
    # Crear y avanzar varios tickets para acumular notifs.
    t_tec = _token(client, tecnico.correo, "Tecnico#2026")
    for _ in range(3):
        tk = client.post(
            "/api/v1/tickets",
            headers=_auth(t_est),
            json={
                "edificio_id": str(edificio.id),
                "aula_id": str(aula.id),
                "tipo_falla": "otro",
            },
        ).json()
        client.patch(
            f"/api/v1/tickets/{tk['id']}",
            headers=_auth(t_tec),
            json={"estado": "en_proceso"},
        )

    notifs_pre = client.get("/api/v1/notificaciones", headers=_auth(t_est)).json()
    assert notifs_pre["total_no_leidas"] == 3

    r = client.post("/api/v1/notificaciones/leer-todas", headers=_auth(t_est)).json()
    assert r["actualizadas"] == 3

    notifs_post = client.get("/api/v1/notificaciones", headers=_auth(t_est)).json()
    assert notifs_post["total_no_leidas"] == 0


def test_no_puedo_marcar_leida_notificacion_ajena(
    client: TestClient,
    estudiante: Usuario,
    tecnico: Usuario,
    edificio: Edificio,
) -> None:
    aula = edificio.pisos[0].aulas[0]
    # Estudiante crea ticket → técnico recibe notif "ticket_creado".
    t_est = _token(client, estudiante.correo, "Estudiante#2026")
    client.post(
        "/api/v1/tickets",
        headers=_auth(t_est),
        json={
            "edificio_id": str(edificio.id),
            "aula_id": str(aula.id),
            "tipo_falla": "otro",
        },
    )

    t_tec = _token(client, tecnico.correo, "Tecnico#2026")
    notif_tec = client.get("/api/v1/notificaciones", headers=_auth(t_tec)).json()
    nid_tec = notif_tec["items"][0]["id"]

    # Estudiante intenta marcar como leída la del técnico.
    resp = client.post(
        f"/api/v1/notificaciones/{nid_tec}/leer", headers=_auth(t_est)
    )
    assert resp.status_code == 404


# =====================================================================
# Robustez: SMTP no configurado no rompe la creación.
# =====================================================================
def test_smtp_apagado_no_rompe_creacion(
    client: TestClient,
    estudiante: Usuario,
    tecnico: Usuario,
    edificio: Edificio,
) -> None:
    """En tests SMTP_HOST está vacío. Nada debe romperse y la notif in-app
    debe crearse igual."""
    aula = edificio.pisos[0].aulas[0]
    t_est = _token(client, estudiante.correo, "Estudiante#2026")
    with patch("smtplib.SMTP") as mocked_smtp:
        resp = client.post(
            "/api/v1/tickets",
            headers=_auth(t_est),
            json={
                "edificio_id": str(edificio.id),
                "aula_id": str(aula.id),
                "tipo_falla": "sin_senal",
            },
        )
    assert resp.status_code == 201
    # SMTP_HOST está vacío, así que NO debió instanciarse el cliente smtp.
    mocked_smtp.assert_not_called()

    # La notificación in-app debe estar ahí.
    t_tec = _token(client, tecnico.correo, "Tecnico#2026")
    notifs = client.get("/api/v1/notificaciones", headers=_auth(t_tec)).json()
    assert notifs["total_no_leidas"] == 1
