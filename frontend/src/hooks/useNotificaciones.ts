import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  notificacionesApi,
  type ListNotificacionesFilters,
} from "@/lib/notificaciones";
import { useAuthStore } from "@/stores/authStore";

const KEY = ["notificaciones"] as const;

/**
 * Lista de notificaciones con polling 15s. Sólo activo cuando hay sesión
 * para no martillar el backend en la pantalla de login.
 */
export function useNotificaciones(filters: ListNotificacionesFilters = {}) {
  const token = useAuthStore((s) => s.token);
  return useQuery({
    queryKey: [...KEY, filters],
    queryFn: () => notificacionesApi.list(filters),
    refetchInterval: 15_000,
    enabled: Boolean(token),
  });
}

export function useMarkNotificacionLeida() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => notificacionesApi.markRead(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

export function useMarkAllNotificacionesLeidas() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => notificacionesApi.markAllRead(),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}
