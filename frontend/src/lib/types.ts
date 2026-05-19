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
}

export interface AuthTokens {
  access_token: string;
  token_type: "bearer";
}
