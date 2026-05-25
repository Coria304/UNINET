"""Endpoints de autenticación (RF009, CU-10)."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models import Usuario
from app.schemas.auth import (
    LoginRequest,
    LoginResponseMFA,
    LoginResponseToken,
    MFAVerifyRequest,
)
from app.schemas.usuario import UsuarioOut
from app.services import audit
from app.services.auth import AuthError, AuthErrorCode, authenticate, verify_mfa

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str | None:
    if request.client:
        return request.client.host
    return None


def _map_auth_error(error: AuthError) -> HTTPException:
    if error.code == AuthErrorCode.INVALID_CREDENTIALS:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos.",
        )
    if error.code == AuthErrorCode.ACCOUNT_LOCKED:
        return HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=(
                f"Cuenta bloqueada temporalmente. Intenta de nuevo en "
                f"{(error.retry_after_seconds or 0) // 60} minutos."
            ),
            headers={"Retry-After": str(error.retry_after_seconds or 0)},
        )
    if error.code == AuthErrorCode.ACCOUNT_INACTIVE:
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta inactiva. Contacta al administrador.",
        )
    if error.code in (AuthErrorCode.INVALID_MFA_CODE, AuthErrorCode.MFA_CHALLENGE_EXPIRED):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código de verificación inválido o expirado.",
        )
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error de autenticación.")


@router.post(
    "/login",
    responses={
        200: {"model": LoginResponseToken, "description": "Login completado."},
        202: {"model": LoginResponseMFA, "description": "Se requiere verificación MFA."},
        401: {"description": "Credenciales inválidas."},
        423: {"description": "Cuenta bloqueada temporalmente."},
    },
)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Inicio de sesión. Devuelve token o reto MFA según el rol."""
    try:
        outcome = authenticate(
            db, correo=payload.correo, password=payload.password, ip=_client_ip(request)
        )
    except AuthError as exc:
        raise _map_auth_error(exc) from exc

    if outcome.requires_mfa:
        body = LoginResponseMFA(
            challenge_id=outcome.challenge_id,  # type: ignore[arg-type]
            dev_code=outcome.dev_code,
        )
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=body.model_dump(mode="json"))

    return LoginResponseToken(
        access_token=outcome.access_token,  # type: ignore[arg-type]
        usuario=UsuarioOut.model_validate(outcome.usuario),
    )


@router.post("/mfa/verify", response_model=LoginResponseToken)
def mfa_verify(payload: MFAVerifyRequest, request: Request, db: Session = Depends(get_db)):
    """Valida el código MFA y emite el token de acceso."""
    try:
        outcome = verify_mfa(
            db, challenge_id=payload.challenge_id, code=payload.code, ip=_client_ip(request)
        )
    except AuthError as exc:
        raise _map_auth_error(exc) from exc

    return LoginResponseToken(
        access_token=outcome.access_token,  # type: ignore[arg-type]
        usuario=UsuarioOut.model_validate(outcome.usuario),
    )


@router.get("/me", response_model=UsuarioOut)
def me(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """Devuelve el usuario autenticado a partir del token."""
    return current_user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Cierra la sesión (registra el evento; el cliente descarta el token)."""
    audit.record_event(
        db, accion="logout", usuario_id=current_user.id, ip_origen=_client_ip(request)
    )
    db.commit()
