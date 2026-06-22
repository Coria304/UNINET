"""Servicio de verificación multifactor (RF009 CA-RF009-3).

Implementación basada en correo: genera un código de 6 dígitos, lo
almacena en Redis con TTL corto y lo "envía" al correo del usuario. En
desarrollo el código se registra en los logs (y se devuelve en el
response cuando ENVIRONMENT != production) para facilitar pruebas.

La integración real con SMTP institucional se hará en Sprint 5
(endurecimiento). El contrato de la API no cambia entre dev y prod.
"""

from __future__ import annotations

import json
import logging
import secrets
import smtplib
from dataclasses import dataclass
from email.mime.text import MIMEText
from uuid import UUID, uuid4

from app.core.config import get_settings
from app.core.redis import get_redis

logger = logging.getLogger(__name__)

_CHALLENGE_PREFIX = "mfa:challenge:"
_CHALLENGE_TTL_SECONDS = 300  # 5 minutos


@dataclass
class MFAChallenge:
    challenge_id: UUID
    usuario_id: UUID
    code: str


def _generate_code() -> str:
    """Genera un código numérico de 6 dígitos uniformemente distribuido."""
    return f"{secrets.randbelow(1_000_000):06d}"


def issue_challenge(usuario_id: UUID, correo: str) -> MFAChallenge:
    """Crea y persiste un reto MFA. Devuelve datos para responder al cliente."""
    challenge = MFAChallenge(
        challenge_id=uuid4(),
        usuario_id=usuario_id,
        code=_generate_code(),
    )

    redis_client = get_redis()
    redis_client.setex(
        _CHALLENGE_PREFIX + str(challenge.challenge_id),
        _CHALLENGE_TTL_SECONDS,
        json.dumps({"usuario_id": str(usuario_id), "code": challenge.code}),
    )

    settings = get_settings()
    if settings.smtp_enabled:
        _send_mfa_email(correo, challenge.code, settings)
    else:
        logger.warning(
            "[DEV] Reto MFA para %s — código=%s (challenge_id=%s)",
            correo,
            challenge.code,
            challenge.challenge_id,
        )

    return challenge


def _send_mfa_email(correo: str, code: str, settings) -> None:
    body = (
        f"Tu código de verificación para UniNet Connect es:\n\n"
        f"    {code}\n\n"
        f"Expira en 5 minutos. Si no solicitaste este código, ignora este mensaje."
    )
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = f"Tu código de acceso UniNet: {code}"
    msg["From"] = settings.SMTP_FROM
    msg["To"] = correo

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM, [correo], msg.as_string())
        logger.info("Código MFA enviado a %s", correo)
    except Exception as exc:
        logger.error("Error enviando MFA a %s: %s", correo, exc)


def verify_challenge(challenge_id: UUID, code: str) -> UUID | None:
    """Verifica un código MFA. Devuelve el usuario_id si es correcto.

    Consume el reto (one-shot): tras intento exitoso o fallido se elimina,
    obligando al cliente a reiniciar el flujo de login si falla.
    """
    redis_client = get_redis()
    key = _CHALLENGE_PREFIX + str(challenge_id)
    raw = redis_client.get(key)
    if raw is None:
        return None

    payload = json.loads(raw)
    redis_client.delete(key)

    if not secrets.compare_digest(payload["code"], code):
        return None
    return UUID(payload["usuario_id"])
