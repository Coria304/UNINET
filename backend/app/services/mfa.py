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
from dataclasses import dataclass
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
    if settings.is_production:
        # TODO Sprint 5: enviar correo institucional vía SMTP.
        logger.info("Reto MFA emitido para %s (correo enviado).", correo)
    else:
        logger.warning(
            "[DEV] Reto MFA para %s — código=%s (challenge_id=%s)",
            correo,
            challenge.code,
            challenge.challenge_id,
        )

    return challenge


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
