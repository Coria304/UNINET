import { api } from "@/lib/api";
import type { Usuario, UsuarioCreate } from "@/lib/types";

export const adminApi = {
  async tecnicos(): Promise<Usuario[]> {
    const r = await api.get<Usuario[]>("/admin/tecnicos");
    return r.data;
  },

  async listarUsuarios(): Promise<Usuario[]> {
    const r = await api.get<Usuario[]>("/admin/usuarios");
    return r.data;
  },

  async crearUsuario(data: UsuarioCreate): Promise<Usuario> {
    const r = await api.post<Usuario>("/admin/usuarios", data);
    return r.data;
  },
};
