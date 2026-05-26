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

// ---------------------------------------------------------------------------
// Reportes admin (RF007)
// ---------------------------------------------------------------------------
export interface ContadorPorEstado {
  activo: number;
  en_proceso: number;
  resuelto: number;
}

export interface BucketEdificio {
  edificio_id: string;
  codigo: string;
  nombre: string;
  total: number;
}

export interface BucketTipoFalla {
  tipo: TipoFalla;
  total: number;
}

export interface PuntoSerieTemporal {
  fecha: string; // ISO
  total: number;
}

export interface ResumenReporte {
  desde: string;
  hasta: string;
  total: number;
  por_estado: ContadorPorEstado;
  mttr_horas: number | null;
  sin_asignar: number;
  top_edificios: BucketEdificio[];
  top_tipos: BucketTipoFalla[];
  serie_temporal: PuntoSerieTemporal[];
  granularidad: "day" | "week" | "month";
}

// ---------------------------------------------------------------------------
// Notificaciones (RF005)
// ---------------------------------------------------------------------------
export type TipoNotificacion =
  | "ticket_creado"
  | "ticket_asignado"
  | "ticket_estado_cambio";

export interface Notificacion {
  id: string;
  tipo: TipoNotificacion;
  titulo: string;
  mensaje: string;
  entidad_tipo: string | null;
  entidad_id: string | null;
  leida: boolean;
  leida_at: string | null;
  created_at: string;
}

export interface NotificacionListResponse {
  items: Notificacion[];
  total_no_leidas: number;
}

/**
 * Etiquetas legibles para el campo `tipo` del aula. Coinciden con los
 * tipos que emite seeds/seed_escom.py. Cualquier tipo no listado se
 * muestra capitalizando la propia palabra.
 */
export const TIPO_AULA_LABEL: Record<string, string> = {
  aula: "Aula",
  laboratorio: "Laboratorio",
  cubiculo: "Cubículo",
  posgrado: "Salón de posgrado",
  computo: "Aula de computadoras",
  unidad_informatica: "Unidad de Informática",
  biblioteca: "Biblioteca",
  auditorio: "Auditorio",
  administracion: "Cubículos administrativos",
};

export function tipoAulaLabel(tipo: string | null | undefined): string {
  if (!tipo) return "";
  return TIPO_AULA_LABEL[tipo] ?? tipo;
}

/**
 * Formato canónico para mostrar un aula en listas/dropdowns.
 *   - "1101 — Unidad de Informática" cuando hay nombre
 *   - "1103 (Laboratorio)" cuando el tipo difiere del default
 *   - "1001" para aulas estándar sin nombre
 */
export function formatAulaLabel(aula: Aula): string {
  if (aula.nombre) return `${aula.codigo} — ${aula.nombre}`;
  if (aula.tipo && aula.tipo !== "aula") {
    return `${aula.codigo} (${tipoAulaLabel(aula.tipo)})`;
  }
  return aula.codigo;
}
