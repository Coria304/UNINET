import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  ticketsApi,
  type ListFilters,
  type TicketCreatePayload,
  type TicketUpdatePayload,
} from "@/lib/tickets";

const KEYS = {
  list: (filters: ListFilters) => ["tickets", "list", filters] as const,
  detail: (id: string) => ["tickets", "detail", id] as const,
};

/**
 * Lista de tickets con polling opcional. Los técnicos/admin típicamente
 * quieren ver cambios sin recargar — pasarles `pollMs: 30_000` en el
 * panel de operaciones.
 */
export function useTicketsList(filters: ListFilters = {}, pollMs?: number) {
  return useQuery({
    queryKey: KEYS.list(filters),
    queryFn: () => ticketsApi.list(filters),
    refetchInterval: pollMs,
  });
}

export function useTicket(id: string | undefined, pollMs?: number) {
  return useQuery({
    queryKey: KEYS.detail(id ?? "none"),
    queryFn: () => ticketsApi.get(id as string),
    enabled: Boolean(id),
    refetchInterval: pollMs,
  });
}

export function useCreateTicket() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: TicketCreatePayload) => ticketsApi.create(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tickets"] });
    },
  });
}

export function useUpdateTicket(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: TicketUpdatePayload) => ticketsApi.update(id, payload),
    onSuccess: (data) => {
      qc.setQueryData(KEYS.detail(id), data);
      qc.invalidateQueries({ queryKey: ["tickets", "list"] });
    },
  });
}
