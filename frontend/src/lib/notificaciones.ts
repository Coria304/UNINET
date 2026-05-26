import { api } from "@/lib/api";
import type { Notificacion, NotificacionListResponse } from "@/lib/types";

export interface ListNotificacionesFilters {
  leida?: boolean;
  limit?: number;
}

export const notificacionesApi = {
  async list(
    filters: ListNotificacionesFilters = {},
  ): Promise<NotificacionListResponse> {
    const r = await api.get<NotificacionListResponse>("/notificaciones", {
      params: filters,
    });
    return r.data;
  },
  async markRead(id: string): Promise<Notificacion> {
    const r = await api.post<Notificacion>(`/notificaciones/${id}/leer`);
    return r.data;
  },
  async markAllRead(): Promise<{ actualizadas: number }> {
    const r = await api.post<{ actualizadas: number }>(
      "/notificaciones/leer-todas",
    );
    return r.data;
  },
};
