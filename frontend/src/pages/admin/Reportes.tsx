import { useMemo, useState } from "react";

import { useResumenReporte } from "@/hooks/useReportes";
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
    <div className="bg-white rounded-lg shadow p-4">
      <div className="text-xs text-slate-500 uppercase tracking-wide">
        {label}
      </div>
      <div className={`text-2xl font-semibold mt-1 ${color}`}>{value}</div>
      {subtitle && (
        <div className="text-xs text-slate-400 mt-0.5">{subtitle}</div>
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
      <p className="text-sm text-slate-500">
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
            <span className="w-20 text-slate-500">
              {fmtFecha(p.fecha, granularidad)}
            </span>
            <div className="flex-1 bg-slate-100 rounded h-3 overflow-hidden">
              <div
                className="bg-brand-500 h-full rounded"
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
        <Card label="Total" value={data.total} color="text-slate-800" />
        <Card label="Activos" value={data.por_estado.activo} color="text-amber-700" />
        <Card label="En proceso" value={data.por_estado.en_proceso} color="text-blue-700" />
        <Card label="Resueltos" value={data.por_estado.resuelto} color="text-emerald-700" />
        <Card
          label="MTTR"
          value={mttrTxt}
          color="text-slate-800"
          subtitle="tiempo medio de resolución"
        />
        <Card
          label="Sin asignar"
          value={data.sin_asignar}
          color={data.sin_asignar > 0 ? "text-red-700" : "text-slate-800"}
        />
      </section>

      {data.total > 0 && (
        <div className="text-sm text-slate-500">
          Tasa de resolución: <strong>{tasaResolucion}%</strong>
        </div>
      )}

      <section className="grid lg:grid-cols-2 gap-4">
        <div className="bg-white rounded-lg shadow p-5">
          <h3 className="font-semibold mb-3">Top edificios con más reportes</h3>
          {data.top_edificios.length === 0 ? (
            <p className="text-sm text-slate-500">Sin datos en el rango.</p>
          ) : (
            <table className="w-full text-sm">
              <tbody>
                {data.top_edificios.map((b) => (
                  <tr
                    key={b.edificio_id}
                    className="border-b border-slate-100 last:border-0"
                  >
                    <td className="py-2 font-medium">{b.codigo}</td>
                    <td className="py-2 text-slate-500">{b.nombre}</td>
                    <td className="py-2 text-right tabular-nums">{b.total}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="bg-white rounded-lg shadow p-5">
          <h3 className="font-semibold mb-3">Tipos de falla</h3>
          {data.top_tipos.length === 0 ? (
            <p className="text-sm text-slate-500">Sin datos en el rango.</p>
          ) : (
            <table className="w-full text-sm">
              <tbody>
                {data.top_tipos.map((b) => (
                  <tr
                    key={b.tipo}
                    className="border-b border-slate-100 last:border-0"
                  >
                    <td className="py-2">{TIPO_FALLA_LABEL[b.tipo]}</td>
                    <td className="py-2 text-right tabular-nums">{b.total}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>

      <section className="bg-white rounded-lg shadow p-5">
        <h3 className="font-semibold mb-3">Tickets por {data.granularidad === "month" ? "mes" : data.granularidad === "week" ? "semana" : "día"}</h3>
        <SerieTemporal puntos={data.serie_temporal} granularidad={data.granularidad} />
      </section>
    </>
  );
}

function Reportes() {
  const [rangoIdx, setRangoIdx] = useState(1); // default: 30 días
  const rango = RANGOS[rangoIdx];

  const filters = useMemo(
    () => ({
      desde: isoHaceDias(rango.days),
      granularidad: rango.granularidad,
    }),
    [rango],
  );

  const { data, isLoading, isError } = useResumenReporte(filters);

  return (
    <div className="space-y-5 max-w-6xl">
      <header className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold">Reportes SLA</h2>
          <p className="text-sm text-slate-500 mt-1">
            Métricas agregadas del sistema de tickets.
          </p>
        </div>
        <div className="flex gap-1 bg-white border border-slate-200 rounded-lg p-0.5">
          {RANGOS.map((r, i) => (
            <button
              key={r.label}
              type="button"
              onClick={() => setRangoIdx(i)}
              className={`px-3 py-1.5 text-sm rounded ${
                i === rangoIdx
                  ? "bg-brand-500 text-white"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
      </header>

      {isLoading && <p className="text-slate-500">Cargando métricas…</p>}
      {isError && (
        <p className="text-red-600">No se pudieron cargar los reportes.</p>
      )}
      {data && <Resumen data={data} />}
    </div>
  );
}

export default Reportes;
