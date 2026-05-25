import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { Rol, Usuario } from "@/lib/types";

interface PendingMfa {
  challengeId: string;
  correo: string;
  expiresAt: number; // epoch ms
  devCode: string | null;
}

interface AuthState {
  token: string | null;
  usuario: Usuario | null;
  pendingMfa: PendingMfa | null;
  login: (token: string, usuario: Usuario) => void;
  setUsuario: (usuario: Usuario) => void;
  setPendingMfa: (pending: PendingMfa | null) => void;
  logout: () => void;
  hasRole: (roles: Rol[]) => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      usuario: null,
      pendingMfa: null,
      login: (token, usuario) => set({ token, usuario, pendingMfa: null }),
      setUsuario: (usuario) => set({ usuario }),
      setPendingMfa: (pending) => set({ pendingMfa: pending }),
      logout: () => set({ token: null, usuario: null, pendingMfa: null }),
      hasRole: (roles) => {
        const rol = get().usuario?.rol;
        return rol ? roles.includes(rol) : false;
      },
    }),
    {
      name: "uninet-auth",
      // No persistimos retos MFA: deben morir con la pestaña.
      partialize: (state) => ({ token: state.token, usuario: state.usuario }),
    },
  ),
);
