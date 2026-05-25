import { api } from "@/lib/api";
import type {
  EstadoTicket,
  PrioridadTicket,
  Ticket,
  TicketListItem,
  TipoFalla,
} from "@/lib/types";

export interface TicketCreatePayload {
  edificio_id: string;
  piso_id?: string | null;
  aula_id?: string | null;
  tipo_falla: TipoFalla;
  descripcion?: string | null;
  latitud?: number | null;
  longitud?: number | null;
}

export interface TicketUpdatePayload {
  estado?: EstadoTicket;
  asignado_a_id?: string | null;
  prioridad?: PrioridadTicket;
  comentario?: string | null;
}

export interface ListFilters {
  estado?: EstadoTicket;
  asignado_a_id?: string;
}

export const ticketsApi = {
  async list(filters: ListFilters = {}): Promise<TicketListItem[]> {
    const r = await api.get<TicketListItem[]>("/tickets", { params: filters });
    return r.data;
  },
  async get(id: string): Promise<Ticket> {
    const r = await api.get<Ticket>(`/tickets/${id}`);
    return r.data;
  },
  async create(payload: TicketCreatePayload): Promise<Ticket> {
    const r = await api.post<Ticket>("/tickets", payload);
    return r.data;
  },
  async update(id: string, payload: TicketUpdatePayload): Promise<Ticket> {
    const r = await api.patch<Ticket>(`/tickets/${id}`, payload);
    return r.data;
  },
};
