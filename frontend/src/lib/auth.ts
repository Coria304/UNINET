import { api } from "@/lib/api";
import type { Usuario } from "@/lib/types";

export interface LoginPayload {
  correo: string;
  password: string;
}

export interface LoginTokenResponse {
  mfa_required: false;
  access_token: string;
  token_type: "bearer";
  usuario: Usuario;
}

export interface LoginMFAResponse {
  mfa_required: true;
  challenge_id: string;
  expires_in: number;
  dev_code: string | null;
}

export type LoginResponse = LoginTokenResponse | LoginMFAResponse;

export interface MFAVerifyPayload {
  challenge_id: string;
  code: string;
}

export const authApi = {
  async login(payload: LoginPayload): Promise<LoginResponse> {
    const response = await api.post<LoginResponse>("/auth/login", payload, {
      // Aceptamos 202 además de 200 para no disparar el error handler.
      validateStatus: (s) => s === 200 || s === 202,
    });
    return response.data;
  },

  async verifyMfa(payload: MFAVerifyPayload): Promise<LoginTokenResponse> {
    const response = await api.post<LoginTokenResponse>(
      "/auth/mfa/verify",
      payload,
    );
    return response.data;
  },

  async me(): Promise<Usuario> {
    const response = await api.get<Usuario>("/auth/me");
    return response.data;
  },

  async logout(): Promise<void> {
    await api.post("/auth/logout");
  },

  async cambiarPassword(payload: { password_actual: string; password_nueva: string }): Promise<void> {
    await api.patch("/auth/password", payload);
  },
};
