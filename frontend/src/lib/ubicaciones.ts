import { api } from "@/lib/api";
import type { Edificio } from "@/lib/types";

export const ubicacionesApi = {
  async listEdificios(): Promise<Edificio[]> {
    const r = await api.get<Edificio[]>("/ubicaciones/edificios");
    return r.data;
  },
};
