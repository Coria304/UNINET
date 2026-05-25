"""Servicio de tickets (RF001 — reporte geolocalizado, RF004 — gestión de tickets).

Orquesta validaciones de ubicación, permisos por rol, transiciones de estado
y registro de historial + audit log. Lanza `TicketError` para que la capa
de API la traduzca a HTTP.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import (
    Aula,
    EstadoTicket,
    PrioridadTicket,
    RolUsuario,
    Ticket,
    Usuario,
)
from app.repositories.ticket import TicketRepository
from app.repositories.ubicacion import AulaRepository, EdificioRepository
from app.repositories.usuario import UsuarioRepository
from app.schemas.ticket import TicketCreate, TicketUpdate
from app.services import audit

# Roles con permisos operativos sobre cualquier ticket.
ROLES_OPERADORES = frozenset({RolUsuario.PERSONAL_TECNICO, RolUsuario.ADMINISTRADOR_TI})

# Transiciones permitidas. `RESUELTO` es terminal — para reabrir hay que
# crear un nuevo ticket (decisión Sprint 2; ampliable en RF007).
TRANSICIONES_VALIDAS: dict[EstadoTicket, frozenset[EstadoTicket]] = {
    EstadoTicket.ACTIVO: frozenset({EstadoTicket.EN_PROCESO, EstadoTicket.RESUELTO}),
    EstadoTicket.EN_PROCESO: frozenset({EstadoTicket.RESUELTO, EstadoTicket.ACTIVO}),
    EstadoTicket.RESUELTO: frozenset(),
}


class TicketErrorCode(str, Enum):
    UBICACION_INVALIDA = "ubicacion_invalida"
    UBICACION_INCOHERENTE = "ubicacion_incoherente"
    TICKET_NO_ENCONTRADO = "ticket_no_encontrado"
    SIN_PERMISO = "sin_permiso"
    TRANSICION_INVALIDA = "transicion_invalida"
    ASIGNADO_INVALIDO = "asignado_invalido"


class TicketError(Exception):
    def __init__(self, code: TicketErrorCode, message: str | None = None) -> None:
        super().__init__(message or code.value)
        self.code = code
        self.message = message or code.value


@dataclass
class _Ubicacion:
    edificio_id: UUID
    piso_id: UUID | None
    aula_id: UUID | None


def _validar_ubicacion(db: Session, payload: TicketCreate) -> _Ubicacion:
    """Valida que aula → piso → edificio sean coherentes entre sí."""
    edif = EdificioRepository(db).get(payload.edificio_id)
    if edif is None:
        raise TicketError(TicketErrorCode.UBICACION_INVALIDA, "Edificio no existe.")

    if payload.aula_id is not None:
        aula: Aula | None = AulaRepository(db).get_with_piso(payload.aula_id)
        if aula is None:
            raise TicketError(TicketErrorCode.UBICACION_INVALIDA, "Aula no existe.")
        if aula.piso.edificio_id != payload.edificio_id:
            raise TicketError(
                TicketErrorCode.UBICACION_INCOHERENTE,
                "El aula no pertenece al edificio indicado.",
            )
        # piso_id es opcional en el payload; si lo mandan, debe coincidir.
        if payload.piso_id is not None and payload.piso_id != aula.piso_id:
            raise TicketError(
                TicketErrorCode.UBICACION_INCOHERENTE,
                "El aula no pertenece al piso indicado.",
            )
        return _Ubicacion(payload.edificio_id, aula.piso_id, aula.id)

    # Sin aula: validamos sólo piso si vino.
    if payload.piso_id is not None:
        from app.models import Piso  # local: evita ciclo de imports a nivel módulo

        piso = db.get(Piso, payload.piso_id)
        if piso is None:
            raise TicketError(TicketErrorCode.UBICACION_INVALIDA, "Piso no existe.")
        if piso.edificio_id != payload.edificio_id:
            raise TicketError(
                TicketErrorCode.UBICACION_INCOHERENTE,
                "El piso no pertenece al edificio indicado.",
            )

    return _Ubicacion(payload.edificio_id, payload.piso_id, None)


def create_ticket(
    db: Session,
    *,
    reportante: Usuario,
    payload: TicketCreate,
    ip: str | None,
) -> Ticket:
    """Crea un ticket desde un reporte y registra el evento inicial."""
    ubicacion = _validar_ubicacion(db, payload)

    ticket = Ticket(
        reportante_id=reportante.id,
        edificio_id=ubicacion.edificio_id,
        piso_id=ubicacion.piso_id,
        aula_id=ubicacion.aula_id,
        tipo_falla=payload.tipo_falla,
        descripcion=payload.descripcion,
        estado=EstadoTicket.ACTIVO,
        prioridad=PrioridadTicket.MEDIA,
        # GPS/geohash: TODO Sprint 5 (cifrado con pgcrypto). Por ahora ignoramos
        # latitud/longitud aunque vengan en el payload, para no almacenar PII
        # en claro. La ubicación efectiva es edificio/piso/aula.
    )
    repo = TicketRepository(db)
    repo.add(ticket)

    repo.append_historico(
        ticket,
        estado_anterior=None,
        estado_nuevo=EstadoTicket.ACTIVO,
        responsable=reportante,
        comentario="Ticket creado a partir de reporte geolocalizado.",
    )

    audit.record_event(
        db,
        accion="ticket_creado",
        usuario_id=reportante.id,
        entidad="ticket",
        entidad_id=ticket.id,
        datos={
            "tipo_falla": payload.tipo_falla.value,
            "edificio_id": str(ubicacion.edificio_id),
            "aula_id": str(ubicacion.aula_id) if ubicacion.aula_id else None,
        },
        ip_origen=ip,
    )
    db.commit()
    db.refresh(ticket)
    return ticket


def get_ticket(db: Session, *, current_user: Usuario, ticket_id: UUID) -> Ticket:
    """Devuelve el detalle si el usuario tiene permiso para verlo."""
    ticket = TicketRepository(db).get_with_detail(ticket_id)
    if ticket is None:
        raise TicketError(TicketErrorCode.TICKET_NO_ENCONTRADO)

    if current_user.rol not in ROLES_OPERADORES and ticket.reportante_id != current_user.id:
        # Estudiantes/docentes solo ven los suyos.
        raise TicketError(TicketErrorCode.SIN_PERMISO)

    return ticket


def list_tickets(
    db: Session,
    *,
    current_user: Usuario,
    estado: EstadoTicket | None = None,
    asignado_a_id: UUID | None = None,
) -> list[Ticket]:
    """Lista tickets respetando el rol del usuario."""
    repo = TicketRepository(db)
    if current_user.rol in ROLES_OPERADORES:
        return repo.list_all(estado=estado, asignado_a_id=asignado_a_id)
    # Estudiante/docente: solo los reportados por él.
    tickets = repo.list_reportados_por(current_user.id)
    if estado is not None:
        tickets = [t for t in tickets if t.estado == estado]
    return tickets


def update_ticket(
    db: Session,
    *,
    current_user: Usuario,
    ticket_id: UUID,
    payload: TicketUpdate,
    ip: str | None,
) -> Ticket:
    """Aplica cambios (estado, asignación, prioridad). Solo operadores."""
    if current_user.rol not in ROLES_OPERADORES:
        raise TicketError(TicketErrorCode.SIN_PERMISO)

    repo = TicketRepository(db)
    ticket = repo.get_with_detail(ticket_id)
    if ticket is None:
        raise TicketError(TicketErrorCode.TICKET_NO_ENCONTRADO)

    estado_anterior = ticket.estado
    cambio_estado = False

    if payload.estado is not None and payload.estado != ticket.estado:
        if payload.estado not in TRANSICIONES_VALIDAS[ticket.estado]:
            raise TicketError(
                TicketErrorCode.TRANSICION_INVALIDA,
                f"No se puede pasar de '{ticket.estado.value}' a '{payload.estado.value}'.",
            )
        ticket.estado = payload.estado
        cambio_estado = True
        if payload.estado == EstadoTicket.RESUELTO:
            repo.mark_closed(ticket)

    if payload.asignado_a_id is not None:
        # asignar a un técnico real (o al propio admin TI).
        asignado = UsuarioRepository(db).get(payload.asignado_a_id)
        if asignado is None or asignado.rol not in ROLES_OPERADORES:
            raise TicketError(
                TicketErrorCode.ASIGNADO_INVALIDO,
                "Solo se puede asignar a personal técnico o admin TI.",
            )
        ticket.asignado_a_id = payload.asignado_a_id

    if payload.prioridad is not None:
        ticket.prioridad = payload.prioridad

    if cambio_estado:
        repo.append_historico(
            ticket,
            estado_anterior=estado_anterior,
            estado_nuevo=ticket.estado,
            responsable=current_user,
            comentario=payload.comentario,
        )

    audit.record_event(
        db,
        accion="ticket_actualizado",
        usuario_id=current_user.id,
        entidad="ticket",
        entidad_id=ticket.id,
        datos={
            "estado_anterior": estado_anterior.value,
            "estado_nuevo": ticket.estado.value,
            "asignado_a_id": str(ticket.asignado_a_id) if ticket.asignado_a_id else None,
            "prioridad": ticket.prioridad.value,
        },
        ip_origen=ip,
    )
    db.commit()
    db.refresh(ticket)
    # Re-cargar con relaciones para el response.
    return repo.get_with_detail(ticket.id)  # type: ignore[return-value]
