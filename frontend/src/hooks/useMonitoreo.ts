import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { alertasApi, monitoreoApi } from "@/lib/monitoreo";

export function useMonitoreoEstado(edificioId?: string) {
  return useQuery({
    queryKey: ["monitoreo", "estado", edificioId],
    queryFn: () => monitoreoApi.estado(edificioId),
    refetchInterval: 15_000, // polling cada 15 s para "real-time"
  });
}

export function useAlertas(soloActivas = true) {
  return useQuery({
    queryKey: ["alertas", { soloActivas }],
    queryFn: () => alertasApi.listar(soloActivas),
    refetchInterval: 30_000,
  });
}

export function useAtenderAlerta() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, comentario }: { id: string; comentario?: string }) =>
      alertasApi.atender(id, comentario),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["alertas"] });
    },
  });
}
