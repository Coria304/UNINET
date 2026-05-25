"""Endpoints de tickets (RF001, RF004)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models import EstadoTicket, Usuario
from app.schemas.ticket import (
    TicketCreate,
    TicketListItem,
    TicketOut,
    TicketUpdate,
)
from app.services.ticket import (
    TicketError,
    TicketErrorCode,
    create_ticket,
    get_ticket,
    list_tickets,
    update_ticket,
)

router = APIRouter(prefix="/tickets", tags=["tickets"])


def _client_ip(request: Request) -> str | None:
    if request.client:
        return request.client.host
    return None


def _map_error(error: TicketError) -> HTTPException:
    if error.code == TicketErrorCode.TICKET_NO_ENCONTRADO:
        return HTTPException(status.HTTP_404_NOT_FOUND, detail="Ticket no encontrado.")
    if error.code == TicketErrorCode.SIN_PERMISO:
        return HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para esta operación sobre el ticket.",
        )
    if error.code in (
        TicketErrorCode.UBICACION_INVALIDA,
        TicketErrorCode.UBICACION_INCOHERENTE,
        TicketErrorCode.TRANSICION_INVALIDA,
        TicketErrorCode.ASIGNADO_INVALIDO,
    ):
        return HTTPException(status.HTTP_400_BAD_REQUEST, detail=error.message)
    return HTTPException(status.HTTP_400_BAD_REQUEST, detail="Error en operación de ticket.")


@router.post(
    "",
    response_model=TicketOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear ticket desde reporte geolocalizado (RF001)",
)
def crear_ticket(
    payload: TicketCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> TicketOut:
    try:
        ticket = create_ticket(
            db, reportante=current_user, payload=payload, ip=_client_ip(request)
        )
    except TicketError as exc:
        raise _map_error(exc) from exc
    # Re-cargar con relaciones para el response.
    from app.repositories.ticket import TicketRepository

    full = TicketRepository(db).get_with_detail(ticket.id)
    return TicketOut.model_validate(full)


@router.get(
    "",
    response_model=list[TicketListItem],
    summary="Listar tickets (filtrado por rol)",
)
def listar_tickets(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    estado: EstadoTicket | None = Query(default=None),
    asignado_a_id: UUID | None = Query(default=None),
) -> list:
    return list_tickets(
        db, current_user=current_user, estado=estado, asignado_a_id=asignado_a_id
    )


@router.get(
    "/{ticket_id}",
    response_model=TicketOut,
    summary="Detalle de un ticket con historial",
)
def detalle_ticket(
    ticket_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> TicketOut:
    try:
        ticket = get_ticket(db, current_user=current_user, ticket_id=ticket_id)
    except TicketError as exc:
        raise _map_error(exc) from exc
    return TicketOut.model_validate(ticket)


@router.patch(
    "/{ticket_id}",
    response_model=TicketOut,
    summary="Actualizar estado, asignación o prioridad (operadores)",
)
def actualizar_ticket(
    ticket_id: UUID,
    payload: TicketUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> TicketOut:
    try:
        ticket = update_ticket(
            db,
            current_user=current_user,
            ticket_id=ticket_id,
            payload=payload,
            ip=_client_ip(request),
        )
    except TicketError as exc:
        raise _map_error(exc) from exc
    return TicketOut.model_validate(ticket)
