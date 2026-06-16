import { keepPreviousData, useQuery } from "@tanstack/react-query";

import {
  reportesApi,
  type MapaCalorFilters,
  type ResumenFilters,
} from "@/lib/reportes";

export function useResumenReporte(filters: ResumenFilters = {}) {
  return useQuery({
    queryKey: ["reportes", "resumen", filters],
    queryFn: () => reportesApi.resumen(filters),
    // Métricas no cambian tan rápido — refresco cada minuto.
    refetchInterval: 60_000,
  });
}

export function useMapaCalor(filters: MapaCalorFilters = {}) {
  return useQuery({
    queryKey: ["reportes", "mapa-calor", filters],
    queryFn: () => reportesApi.mapaCalor(filters),
    refetchInterval: 60_000,
    placeholderData: keepPreviousData,
  });
}
