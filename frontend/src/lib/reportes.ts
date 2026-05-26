import { api } from "@/lib/api";
import type { ResumenReporte } from "@/lib/types";

export interface ResumenFilters {
  desde?: string; // ISO 8601
  hasta?: string;
  granularidad?: "day" | "week" | "month";
}

export const reportesApi = {
  async resumen(filters: ResumenFilters = {}): Promise<ResumenReporte> {
    const r = await api.get<ResumenReporte>("/reportes/resumen", {
      params: filters,
    });
    return r.data;
  },
};
