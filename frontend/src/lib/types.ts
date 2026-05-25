/** Roles del sistema según RF009. */
export type Rol =
  | "administrador_ti"
  | "personal_tecnico"
  | "docente"
  | "estudiante";

export interface Usuario {
  id: string;
  correo: string;
  nombre_completo: string;
  rol: Rol;
  activo?: boolean;
  last_login_at?: string | null;
}

export interface AuthTokens {
  access_token: string;
  token_type: "bearer";
}

// ---------------------------------------------------------------------------
// Tickets (RF001, RF004)
// ---------------------------------------------------------------------------
export type TipoFalla = "sin_senal" | "lentitud" | "desconexion_intermitente" | "otro";
export type EstadoTicket = "activo" | "en_proceso" | "resuelto";
export type PrioridadTicket = "alta" | "media" | "baja";

export const TIPO_FALLA_LABEL: Record<TipoFalla, string> = {
  sin_senal: "Sin señal",
  lentitud: "Lentitud",
  desconexion_intermitente: "Desconexiones intermitentes",
  otro: "Otro",
};

export const ESTADO_LABEL: Record<EstadoTicket, string> = {
  activo: "Activo",
  en_proceso: "En proceso",
  resuelto: "Resuelto",
};

export const ESTADO_COLOR: Record<EstadoTicket, string> = {
  activo: "bg-amber-100 text-amber-800",
  en_proceso: "bg-blue-100 text-blue-800",
  resuelto: "bg-green-100 text-green-800",
};

export interface TicketHistorico {
  id: string;
  estado_anterior: EstadoTicket | null;
  estado_nuevo: EstadoTicket;
  comentario: string | null;
  responsable_id: string | null;
  fecha: string;
}

export interface TicketListItem {
  id: string;
  tipo_falla: TipoFalla;
  estado: EstadoTicket;
  prioridad: PrioridadTicket;
  edificio_id: string;
  piso_id: string | null;
  aula_id: string | null;
  reportante_id: string;
  asignado_a_id: string | null;
  descripcion: string | null;
  geohash: string | null;
  created_at: string;
  cerrado_at: string | null;
}

export interface Ticket {
  id: string;
  reportante: Usuario;
  asignado_a: Usuario | null;
  edificio_id: string;
  piso_id: string | null;
  aula_id: string | null;
  tipo_falla: TipoFalla;
  descripcion: string | null;
  estado: EstadoTicket;
  prioridad: PrioridadTicket;
  geohash: string | null;
  created_at: string;
  updated_at: string;
  cerrado_at: string | null;
  historico: TicketHistorico[];
}

// ---------------------------------------------------------------------------
// Ubicaciones (RF001)
// ---------------------------------------------------------------------------
export interface Aula {
  id: string;
  codigo: string;
  nombre: string | null;
  tipo: string | null;
}

export interface Piso {
  id: string;
  numero: number;
  nombre: string;
  aulas: Aula[];
}

export interface Edificio {
  id: string;
  codigo: string;
  nombre: string;
  descripcion: string | null;
  latitud: number | null;
  longitud: number | null;
  pisos: Piso[];
}
