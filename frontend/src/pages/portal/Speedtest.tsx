import { useState } from "react";

import { useHistorialSpeedtest, useInvalidateSpeedtest } from "@/hooks/useSpeedtest";
import {
  medirBajada,
  medirLatencia,
  medirSubida,
  speedtestApi,
} from "@/lib/speedtest";

type Fase = "idle" | "ping" | "bajada" | "subida" | "guardando" | "listo" | "error";

interface Resultado {
  latenciaMs: number;
  bajadaMbps: number;
  subidaMbps: number;
}

function MetricCard({
  label,
  valor,
  unidad,
  activo,
}: {
  label: string;
  valor: number | null;
  unidad: string;
  activo: boolean;
}) {
  return (
    <div
      className={`bg-white rounded-lg shadow p-6 text-center transition-all ${
        activo ? "ring-2 ring-brand-500" : ""
      }`}
    >
      <div className="text-xs text-slate-500 uppercase tracking-wide mb-3">
        {label}
      </div>
      {activo ? (
        <div className="text-xl font-semibold text-brand-500 animate-pulse">
          Midiendo…
        </div>
      ) : valor !== null ? (
        <div className="text-3xl font-bold tabular-nums">
          {valor.toFixed(1)}{" "}
          <span className="text-base font-normal text-slate-500">{unidad}</span>
        </div>
      ) : (
        <div className="text-3xl text-slate-200">—</div>
      )}
    </div>
  );
}

function Speedtest() {
  const [fase, setFase] = useState<Fase>("idle");
  const [resultado, setResultado] = useState<Resultado | null>(null);
  const { data: historial, isLoading: cargandoHistorial } =
    useHistorialSpeedtest();
  const invalidate = useInvalidateSpeedtest();

  async function iniciarPrueba() {
    setFase("ping");
    setResultado(null);
    try {
      const latenciaMs = await medirLatencia();
      setFase("bajada");
      const bajadaMbps = await medirBajada();
      setFase("subida");
      const subidaMbps = await medirSubida();
      setFase("guardando");
      await speedtestApi.guardarResultado({
        latencia_ms: Math.round(latenciaMs * 10) / 10,
        velocidad_bajada_mbps: Math.round(bajadaMbps * 10) / 10,
        velocidad_subida_mbps: Math.round(subidaMbps * 10) / 10,
      });
      setResultado({ latenciaMs, bajadaMbps, subidaMbps });
      setFase("listo");
      invalidate();
    } catch {
      setFase("error");
    }
  }

  const corriendo = ["ping", "bajada", "subida", "guardando"].includes(fase);

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h2 className="text-2xl font-semibold">Prueba de velocidad</h2>
        <p className="text-sm text-slate-500 mt-1">
          Mide tu conexión a la red Wi-Fi del campus ESCOM.
        </p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <MetricCard
          label="Latencia"
          valor={resultado ? Math.round(resultado.latenciaMs) : null}
          unidad="ms"
          activo={fase === "ping"}
        />
        <MetricCard
          label="Descarga"
          valor={resultado ? resultado.bajadaMbps : null}
          unidad="Mbps"
          activo={fase === "bajada"}
        />
        <MetricCard
          label="Subida"
          valor={resultado ? resultado.subidaMbps : null}
          unidad="Mbps"
          activo={fase === "subida"}
        />
      </div>

      <div className="text-center">
        {fase === "error" && (
          <p className="text-sm text-red-600 mb-3">
            No se pudo completar la prueba. Verifica tu conexión e intenta de
            nuevo.
          </p>
        )}
        {fase === "guardando" && (
          <p className="text-sm text-slate-500 mb-3">Guardando resultado…</p>
        )}
        <button
          type="button"
          onClick={iniciarPrueba}
          disabled={corriendo}
          className="px-8 py-3 bg-brand-500 text-white rounded-lg font-medium hover:bg-brand-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {corriendo
            ? "Midiendo…"
            : fase === "listo"
              ? "Repetir prueba"
              : "Iniciar prueba"}
        </button>
      </div>

      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-sm font-medium text-slate-700 mb-3">
          Historial de pruebas
        </h3>
        {cargandoHistorial ? (
          <p className="text-sm text-slate-500">Cargando…</p>
        ) : !historial?.length ? (
          <p className="text-sm text-slate-500">
            Aún no tienes pruebas registradas.
          </p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-500 border-b">
                <th className="pb-2 font-medium">Fecha</th>
                <th className="pb-2 font-medium text-right">↓ Mbps</th>
                <th className="pb-2 font-medium text-right">↑ Mbps</th>
                <th className="pb-2 font-medium text-right">Latencia</th>
              </tr>
            </thead>
            <tbody>
              {historial.map((r) => (
                <tr key={r.id} className="border-b last:border-0">
                  <td className="py-2">
                    {new Date(r.ejecutado_at).toLocaleString("es-MX", {
                      dateStyle: "short",
                      timeStyle: "short",
                    })}
                  </td>
                  <td className="py-2 text-right tabular-nums">
                    {r.velocidad_bajada_mbps.toFixed(1)}
                  </td>
                  <td className="py-2 text-right tabular-nums">
                    {r.velocidad_subida_mbps.toFixed(1)}
                  </td>
                  <td className="py-2 text-right tabular-nums">
                    {r.latencia_ms.toFixed(0)} ms
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default Speedtest;
