import { useMemo, useState } from "react";

import { useResumenReporte } from "@/hooks/useReportes";
import { api } from "@/lib/api";
import type { PuntoSerieTemporal, ResumenReporte } from "@/lib/types";
import { TIPO_FALLA_LABEL } from "@/lib/types";

type Granularidad = "day" | "week" | "month";

interface Rango {
  label: string;
  days: number;
  granularidad: Granularidad;
}

const RANGOS: Rango[] = [
  { label: "Últimos 7 días", days: 7, granularidad: "day" },
  { label: "Últimos 30 días", days: 30, granularidad: "day" },
  { label: "Últimos 90 días", days: 90, granularidad: "week" },
];

function isoHaceDias(dias: number): string {
  return new Date(Date.now() - dias * 24 * 3600 * 1000).toISOString();
}

function fmtFecha(iso: string, granularidad: Granularidad): string {
  const d = new Date(iso);
  if (granularidad === "month") {
    return d.toLocaleDateString("es-MX", { month: "short", year: "numeric" });
  }
  return d.toLocaleDateString("es-MX", {
    month: "short",
    day: "numeric",
  });
}

function Card({
  label,
  value,
  color,
  subtitle,
}: {
  label: string;
  value: number | string;
  color: string;
  subtitle?: string;
}) {
  return (
    <div className="card p-4">
      <div className="text-xs text-[#787774] uppercase tracking-wide">
        {label}
      </div>
      <div className={`text-2xl font-semibold tabular-nums mt-1 ${color}`}>{value}</div>
      {subtitle && (
        <div className="text-xs text-[#AAAAAA] mt-0.5">{subtitle}</div>
      )}
    </div>
  );
}

/** Barras CSS puras para no introducir librería de gráficos. */
function SerieTemporal({
  puntos,
  granularidad,
}: {
  puntos: PuntoSerieTemporal[];
  granularidad: Granularidad;
}) {
  const max = useMemo(
    () => puntos.reduce((acc, p) => Math.max(acc, p.total), 0) || 1,
    [puntos],
  );

  if (puntos.length === 0) {
    return (
      <p className="text-sm text-[#787774]">
        Sin tickets en el rango seleccionado.
      </p>
    );
  }

  return (
    <ul className="space-y-1">
      {puntos.map((p) => {
        const pct = Math.round((p.total / max) * 100);
        return (
          <li
            key={p.fecha}
            className="flex items-center gap-2 text-xs"
            aria-label={`${fmtFecha(p.fecha, granularidad)}: ${p.total} tickets`}
          >
            <span className="w-20 text-[#787774]">
              {fmtFecha(p.fecha, granularidad)}
            </span>
            <div className="flex-1 bg-[#EAEAEA] rounded h-3 overflow-hidden">
              <div
                className="bg-[#111111] h-full rounded"
                style={{ width: `${pct}%` }}
              />
            </div>
            <span className="w-8 text-right font-medium tabular-nums">
              {p.total}
            </span>
          </li>
        );
      })}
    </ul>
  );
}

function Resumen({ data }: { data: ResumenReporte }) {
  const tasaResolucion =
    data.total > 0 ? Math.round((data.por_estado.resuelto / data.total) * 100) : 0;
  const mttrTxt =
    data.mttr_horas !== null && data.mttr_horas !== undefined
      ? `${data.mttr_horas} h`
      : "—";

  return (
    <>
      <section className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <Card label="Total" value={data.total} color="text-[#111111]" />
        <Card label="Activos" value={data.por_estado.activo} color="text-amber-700" />
        <Card label="En proceso" value={data.por_estado.en_proceso} color="text-blue-700" />
        <Card label="Resueltos" value={data.por_estado.resuelto} color="text-emerald-700" />
        <Card
          label="MTTR"
          value={mttrTxt}
          color="text-[#111111]"
          subtitle="tiempo medio de resolución"
        />
        <Card
          label="Sin asignar"
          value={data.sin_asignar}
          color={data.sin_asignar > 0 ? "text-red-700" : "text-[#111111]"}
        />
      </section>

      {data.total > 0 && (
        <div className="text-sm text-[#787774]">
          Tasa de resolución: <strong className="text-[#111111]">{tasaResolucion}%</strong>
        </div>
      )}

      <section className="grid lg:grid-cols-2 gap-4">
        <div className="card p-5">
          <h3 className="font-semibold mb-3 text-sm text-[#111111]">Top edificios con más reportes</h3>
          {data.top_edificios.length === 0 ? (
            <p className="text-sm text-[#AAAAAA]">Sin datos en el rango.</p>
          ) : (
            <table className="w-full text-sm">
              <tbody>
                {data.top_edificios.map((b) => (
                  <tr key={b.edificio_id} className="border-b border-[#EAEAEA] last:border-0">
                    <td className="py-2 font-medium">{b.codigo}</td>
                    <td className="py-2 text-[#787774]">{b.nombre}</td>
                    <td className="py-2 text-right tabular-nums font-medium">{b.total}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="card p-5">
          <h3 className="font-semibold mb-3 text-sm text-[#111111]">Tipos de falla</h3>
          {data.top_tipos.length === 0 ? (
            <p className="text-sm text-[#AAAAAA]">Sin datos en el rango.</p>
          ) : (
            <table className="w-full text-sm">
              <tbody>
                {data.top_tipos.map((b) => (
                  <tr key={b.tipo} className="border-b border-[#EAEAEA] last:border-0">
                    <td className="py-2 text-[#787774]">{TIPO_FALLA_LABEL[b.tipo]}</td>
                    <td className="py-2 text-right tabular-nums font-medium">{b.total}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>

      <section className="card p-5">
        <h3 className="font-semibold mb-3 text-sm text-[#111111]">
          Tickets por {data.granularidad === "month" ? "mes" : data.granularidad === "week" ? "semana" : "día"}
        </h3>
        <SerieTemporal puntos={data.serie_temporal} granularidad={data.granularidad} />
      </section>
    </>
  );
}

function Reportes() {
  const [rangoIdx, setRangoIdx] = useState(1); // default: 30 días
  const [descargando, setDescargando] = useState(false);
  const rango = RANGOS[rangoIdx];

  const filters = useMemo(
    () => ({
      desde: isoHaceDias(rango.days),
      granularidad: rango.granularidad,
    }),
    [rango],
  );

  const { data, isLoading, isError } = useResumenReporte(filters);

  async function descargarPdf() {
    setDescargando(true);
    try {
      const r = await api.get("/reportes/pdf", {
        params: filters,
        responseType: "blob",
      });
      const url = URL.createObjectURL(r.data as Blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `reporte-uninet-${new Date().toISOString().slice(0, 10)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setDescargando(false);
    }
  }

  return (
    <div className="space-y-5 max-w-6xl">
      <header className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold">Reportes SLA</h2>
          <p className="text-sm text-[#787774] mt-1">
            Métricas agregadas del sistema de tickets.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex gap-1 bg-white border border-[#EAEAEA] rounded-lg p-0.5">
            {RANGOS.map((r, i) => (
              <button
                key={r.label}
                type="button"
                onClick={() => setRangoIdx(i)}
                className={`px-3 py-1.5 text-sm rounded ${
                  i === rangoIdx
                    ? "bg-[#111111] text-white"
                    : "text-[#787774] hover:bg-[#F7F6F3]"
                }`}
              >
                {r.label}
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={descargarPdf}
            disabled={descargando || !data}
            className="btn-secondary text-xs px-3 py-1.5"
          >
            {descargando ? "Generando…" : "Descargar PDF"}
          </button>
        </div>
      </header>

      {isLoading && <p className="text-[#787774]">Cargando métricas…</p>}
      {isError && (
        <p className="text-red-600">No se pudieron cargar los reportes.</p>
      )}
      {data && <Resumen data={data} />}
    </div>
  );
}

export default Reportes;
