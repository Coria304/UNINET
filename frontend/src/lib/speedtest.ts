import { api } from "@/lib/api";

export interface SpeedtestResultadoIn {
  velocidad_bajada_mbps: number;
  velocidad_subida_mbps: number;
  latencia_ms: number;
  edificio_id?: string;
  piso_id?: string;
  aula_id?: string;
}

export interface SpeedtestResultadoOut {
  id: string;
  usuario_id: string;
  edificio_id: string | null;
  piso_id: string | null;
  aula_id: string | null;
  velocidad_bajada_mbps: number;
  velocidad_subida_mbps: number;
  latencia_ms: number;
  ip_origen: string | null;
  ejecutado_at: string;
}

const BLOB_MB = 5;
const PING_COUNT = 5;

export async function medirLatencia(): Promise<number> {
  const tiempos: number[] = [];
  for (let i = 0; i < PING_COUNT; i++) {
    const t0 = performance.now();
    await api.get("/speedtest/ping");
    tiempos.push(performance.now() - t0);
  }
  return tiempos.reduce((a, b) => a + b, 0) / tiempos.length;
}

export async function medirBajada(): Promise<number> {
  const t0 = performance.now();
  await api.get(`/speedtest/blob?size_mb=${BLOB_MB}`, {
    responseType: "arraybuffer",
  });
  const elapsed = (performance.now() - t0) / 1000;
  return (BLOB_MB * 8) / elapsed;
}

export async function medirSubida(): Promise<number> {
  const payload = new Uint8Array(BLOB_MB * 1024 * 1024);
  const t0 = performance.now();
  await api.post("/speedtest/blob", payload, {
    headers: { "Content-Type": "application/octet-stream" },
  });
  const elapsed = (performance.now() - t0) / 1000;
  return (BLOB_MB * 8) / elapsed;
}

export const speedtestApi = {
  async guardarResultado(
    datos: SpeedtestResultadoIn,
  ): Promise<SpeedtestResultadoOut> {
    const r = await api.post<SpeedtestResultadoOut>(
      "/speedtest/resultado",
      datos,
    );
    return r.data;
  },

  async historial(): Promise<SpeedtestResultadoOut[]> {
    const r = await api.get<SpeedtestResultadoOut[]>("/speedtest/historial");
    return r.data;
  },
};
