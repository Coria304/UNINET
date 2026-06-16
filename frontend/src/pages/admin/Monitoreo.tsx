import { useMonitoreoEstado } from "@/hooks/useMonitoreo";
import { useEdificios } from "@/hooks/useUbicaciones";
import type { AccessPointEstado } from "@/lib/monitoreo";
import { useState } from "react";

const SEMAFORO: Record<string, { bg: string; text: string; label: string }> = {
  good:      { bg: "bg-emerald-50",  text: "text-emerald-700", label: "Normal" },
  high:      { bg: "bg-amber-50",    text: "text-amber-700",   label: "Carga alta" },
  saturated: { bg: "bg-red-50",      text: "text-red-700",     label: "Saturado" },
};

function Semaforo({ estado }: { estado: string }) {
  const s = SEMAFORO[estado] ?? SEMAFORO.good;
  return (
    <span className={`badge ${s.bg} ${s.text}`}>
      {s.label}
    </span>
  );
}

function APRow({ ap }: { ap: AccessPointEstado }) {
  const m = ap.ultima_metrica;
  return (
    <tr className="border-b border-[#EAEAEA] hover:bg-[#F7F6F3]">
      <td className="px-4 py-3">
        <div className="font-medium text-sm">{ap.codigo}</div>
        <div className="text-xs text-[#787774]">{ap.nombre}</div>
      </td>
      <td className="px-4 py-3 text-sm text-[#787774]">
        {ap.edificio_codigo ?? "—"}
      </td>
      <td className="px-4 py-3 text-xs text-[#787774]">{ap.banda}</td>
      <td className="px-4 py-3">
        {m ? (
          <Semaforo estado={m.estado_semaforo} />
        ) : (
          <span className="badge bg-[#F4F3F0] text-[#AAAAAA]">Sin datos</span>
        )}
      </td>
      <td className="px-4 py-3 tabular-nums text-sm text-right">
        {m ? `${m.carga_pct.toFixed(0)}%` : "—"}
      </td>
      <td className="px-4 py-3 tabular-nums text-sm text-right">
        {m ? `${m.latencia_ms.toFixed(0)} ms` : "—"}
      </td>
      <td className="px-4 py-3 tabular-nums text-sm text-right">
        {m ? `${m.ancho_banda_mbps.toFixed(1)}` : "—"}
      </td>
      <td className="px-4 py-3 tabular-nums text-sm text-right">
        {m ? m.clientes_conectados : "—"}
      </td>
    </tr>
  );
}

function Monitoreo() {
  const [edificioId, setEdificioId] = useState("");
  const { data, isLoading, isError, dataUpdatedAt } = useMonitoreoEstado(
    edificioId || undefined,
  );
  const { data: edificios } = useEdificios();

  const updatedLabel = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString("es-MX", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      })
    : null;

  return (
    <div className="space-y-5 max-w-6xl">
      <header className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-2xl font-semibold">Monitoreo de red</h2>
          <p className="text-sm text-[#787774] mt-1">
            Estado de los puntos de acceso. Actualiza cada 15 s.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {updatedLabel && (
            <span className="text-xs text-[#AAAAAA]">
              Última actualización: {updatedLabel}
            </span>
          )}
          <select
            className="input-base !w-auto text-sm"
            value={edificioId}
            onChange={(e) => setEdificioId(e.target.value)}
          >
            <option value="">Todos los edificios</option>
            {edificios?.map((e) => (
              <option key={e.id} value={e.id}>
                {e.codigo} — {e.nombre}
              </option>
            ))}
          </select>
        </div>
      </header>

      {/* Tarjetas de resumen */}
      {data && (
        <section className="grid grid-cols-3 gap-4">
          <div className="card p-4">
            <div className="text-xs text-[#787774] uppercase tracking-wide">
              Total APs
            </div>
            <div className="text-2xl font-semibold tabular-nums mt-1">{data.total}</div>
          </div>
          <div className="card p-4">
            <div className="text-xs text-[#787774] uppercase tracking-wide">
              Activos
            </div>
            <div className="text-2xl font-semibold tabular-nums mt-1 text-emerald-700">
              {data.activos}
            </div>
          </div>
          <div className="card p-4">
            <div className="text-xs text-[#787774] uppercase tracking-wide">
              Con alertas
            </div>
            <div
              className={`text-2xl font-semibold tabular-nums mt-1 ${
                data.con_alertas > 0 ? "text-red-700" : "text-[#111111]"
              }`}
            >
              {data.con_alertas}
            </div>
          </div>
        </section>
      )}

      {isLoading && <p className="text-[#787774] text-sm">Cargando…</p>}
      {isError && (
        <p className="text-red-600 text-sm">
          No se pudo obtener el estado de la red.
        </p>
      )}

      {data && (
        <div className="card overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="text-left text-[#787774] border-b border-[#EAEAEA]">
              <tr>
                <th className="px-4 py-2 font-medium">Access Point</th>
                <th className="px-4 py-2 font-medium">Edificio</th>
                <th className="px-4 py-2 font-medium">Banda</th>
                <th className="px-4 py-2 font-medium">Estado</th>
                <th className="px-4 py-2 font-medium text-right">Carga</th>
                <th className="px-4 py-2 font-medium text-right">Latencia</th>
                <th className="px-4 py-2 font-medium text-right">Mbps</th>
                <th className="px-4 py-2 font-medium text-right">Clientes</th>
              </tr>
            </thead>
            <tbody>
              {data.access_points.length === 0 ? (
                <tr>
                  <td
                    colSpan={8}
                    className="px-4 py-8 text-center text-[#787774]"
                  >
                    No hay access points registrados.
                  </td>
                </tr>
              ) : (
                data.access_points.map((ap) => <APRow key={ap.id} ap={ap} />)
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default Monitoreo;
