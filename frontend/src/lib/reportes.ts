import { api } from "@/lib/api";
import type { MapaCalorResponse, ResumenReporte } from "@/lib/types";

export interface ResumenFilters {
  desde?: string; // ISO 8601
  hasta?: string;
  granularidad?: "day" | "week" | "month";
}

export interface MapaCalorFilters {
  desde?: string;
  hasta?: string;
  edificio_id?: string;
}

export const reportesApi = {
  async resumen(filters: ResumenFilters = {}): Promise<ResumenReporte> {
    const r = await api.get<ResumenReporte>("/reportes/resumen", {
      params: filters,
    });
    return r.data;
  },
  async mapaCalor(
    filters: MapaCalorFilters = {},
  ): Promise<MapaCalorResponse> {
    const r = await api.get<MapaCalorResponse>("/reportes/mapa-calor", {
      params: filters,
    });
    return r.data;
  },
};
