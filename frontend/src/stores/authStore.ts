import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { Rol, Usuario } from "@/lib/types";

interface AuthState {
  token: string | null;
  usuario: Usuario | null;
  login: (token: string, usuario: Usuario) => void;
  logout: () => void;
  hasRole: (roles: Rol[]) => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      usuario: null,
      login: (token, usuario) => set({ token, usuario }),
      logout: () => set({ token: null, usuario: null }),
      hasRole: (roles) => {
        const rol = get().usuario?.rol;
        return rol ? roles.includes(rol) : false;
      },
    }),
    { name: "uninet-auth" },
  ),
);
