import { useQuery } from "@tanstack/react-query";

import { reportesApi, type ResumenFilters } from "@/lib/reportes";

export function useResumenReporte(filters: ResumenFilters = {}) {
  return useQuery({
    queryKey: ["reportes", "resumen", filters],
    queryFn: () => reportesApi.resumen(filters),
    // Métricas no cambian tan rápido — refresco cada minuto.
    refetchInterval: 60_000,
  });
}
