import { api } from "@/lib/api";

export interface MetricaResumen {
  ts: string;
  ancho_banda_mbps: number;
  latencia_ms: number;
  carga_pct: number;
  clientes_conectados: number;
  estado_semaforo: "good" | "high" | "saturated";
}

export interface AccessPointEstado {
  id: string;
  codigo: string;
  nombre: string;
  edificio_id: string | null;
  edificio_codigo: string | null;
  piso_id: string | null;
  latitud: number | null;
  longitud: number | null;
  activo: boolean;
  banda: string;
  ultima_metrica: MetricaResumen | null;
}

export interface MonitoreoResponse {
  total: number;
  activos: number;
  con_alertas: number;
  access_points: AccessPointEstado[];
}

export interface AlertaOut {
  id: string;
  access_point_id: string;
  ap_codigo: string;
  ap_nombre: string;
  edificio_codigo: string | null;
  tipo: string;
  estado: string;
  umbral_violado: number;
  valor_observado: number;
  detectada_at: string;
  atendida_at: string | null;
  comentario_resolucion: string | null;
}

export const monitoreoApi = {
  async estado(edificio_id?: string): Promise<MonitoreoResponse> {
    const r = await api.get<MonitoreoResponse>("/monitoreo/estado", {
      params: edificio_id ? { edificio_id } : undefined,
    });
    return r.data;
  },
};

export const alertasApi = {
  async listar(solo_activas = true): Promise<AlertaOut[]> {
    const r = await api.get<AlertaOut[]>("/alertas", {
      params: { solo_activas },
    });
    return r.data;
  },

  async atender(
    id: string,
    comentario?: string,
  ): Promise<AlertaOut> {
    const r = await api.patch<AlertaOut>(`/alertas/${id}/atender`, {
      comentario_resolucion: comentario ?? null,
    });
    return r.data;
  },
};
