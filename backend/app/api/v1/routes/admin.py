"""Endpoints administrativos."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.security import hash_password
from app.models import RolUsuario, Usuario
from app.repositories.usuario import UsuarioRepository
from app.schemas.usuario import UsuarioCreate, UsuarioOut
from app.services.notificacion import send_credentials_email

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/ping",
    response_model=UsuarioOut,
    summary="Verifica que el usuario tiene rol Administrador TI",
)
def admin_ping(
    current_user: Usuario = Depends(require_roles(RolUsuario.ADMINISTRADOR_TI)),
) -> Usuario:
    return current_user


@router.get(
    "/tecnicos",
    response_model=list[UsuarioOut],
    summary="Lista de técnicos activos disponibles para asignación de tickets",
)
def listar_tecnicos(
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles(RolUsuario.ADMINISTRADOR_TI)),
) -> list[UsuarioOut]:
    tecnicos = list(
        db.scalars(
            select(Usuario)
            .where(
                Usuario.rol == RolUsuario.PERSONAL_TECNICO,
                Usuario.activo.is_(True),
            )
            .order_by(Usuario.nombre_completo)
        )
    )
    return [UsuarioOut.model_validate(t) for t in tecnicos]


@router.get(
    "/usuarios",
    response_model=list[UsuarioOut],
    summary="Lista todos los usuarios excepto administradores",
)
def listar_usuarios(
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles(RolUsuario.ADMINISTRADOR_TI)),
) -> list[UsuarioOut]:
    usuarios = list(
        db.scalars(
            select(Usuario)
            .where(Usuario.rol != RolUsuario.ADMINISTRADOR_TI)
            .order_by(Usuario.nombre_completo)
        )
    )
    return [UsuarioOut.model_validate(u) for u in usuarios]


@router.post(
    "/usuarios",
    response_model=UsuarioOut,
    status_code=201,
    summary="Da de alta un técnico, estudiante o docente",
)
def crear_usuario(
    payload: UsuarioCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles(RolUsuario.ADMINISTRADOR_TI)),
) -> UsuarioOut:
    repo = UsuarioRepository(db)
    if repo.get_by_correo(str(payload.correo)):
        raise HTTPException(status_code=409, detail="Ya existe un usuario con ese correo")

    nuevo = Usuario(
        correo=str(payload.correo).lower(),
        nombre_completo=payload.nombre_completo,
        password_hash=hash_password(payload.password),
        rol=payload.rol,
    )
    repo.add(nuevo)
    db.commit()
    send_credentials_email(nuevo.correo, nuevo.nombre_completo, payload.password)
    return UsuarioOut.model_validate(nuevo)
