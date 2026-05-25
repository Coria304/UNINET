import { Link } from "react-router-dom";

import { useTicketsList } from "@/hooks/useTickets";
import { useEdificios } from "@/hooks/useUbicaciones";
import {
  ESTADO_COLOR,
  ESTADO_LABEL,
  TIPO_FALLA_LABEL,
  type Edificio,
} from "@/lib/types";

function formatFecha(iso: string): string {
  return new Date(iso).toLocaleString("es-MX", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function buildUbicacionLookup(edificios: Edificio[] | undefined) {
  const edif = new Map<string, string>();
  const aulas = new Map<string, string>();
  edificios?.forEach((e) => {
    edif.set(e.id, e.codigo);
    e.pisos.forEach((p) =>
      p.aulas.forEach((a) => aulas.set(a.id, a.codigo)),
    );
  });
  return { edif, aulas };
}

function MisReportes() {
  const { data: tickets, isLoading } = useTicketsList();
  const { data: edificios } = useEdificios();
  const lookup = buildUbicacionLookup(edificios);

  if (isLoading) return <p className="text-slate-500">Cargando reportes…</p>;

  return (
    <div className="space-y-4 max-w-4xl">
      <header className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">Mis reportes</h2>
        <Link to="/portal/reportar" className="text-sm text-brand-600 underline">
          + Crear nuevo
        </Link>
      </header>

      {tickets && tickets.length === 0 && (
        <div className="bg-white rounded-lg shadow p-6 text-center text-slate-500">
          Aún no has reportado ninguna falla.{" "}
          <Link to="/portal/reportar" className="text-brand-600 underline">
            Reporta la primera
          </Link>
          .
        </div>
      )}

      <ul className="space-y-3">
        {tickets?.map((t) => (
          <li key={t.id} className="bg-white rounded-lg shadow p-4">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-medium">
                    {TIPO_FALLA_LABEL[t.tipo_falla]}
                  </span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded ${ESTADO_COLOR[t.estado]}`}
                  >
                    {ESTADO_LABEL[t.estado]}
                  </span>
                </div>
                <div className="text-sm text-slate-600">
                  Edificio <strong>{lookup.edif.get(t.edificio_id) ?? "?"}</strong>
                  {t.aula_id && (
                    <>
                      {" · Aula "}
                      <strong>{lookup.aulas.get(t.aula_id) ?? "?"}</strong>
                    </>
                  )}
                </div>
                {t.descripcion && (
                  <p className="text-sm text-slate-500 mt-1 line-clamp-2">
                    {t.descripcion}
                  </p>
                )}
              </div>
              <div className="text-xs text-slate-400 whitespace-nowrap text-right">
                {formatFecha(t.created_at)}
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default MisReportes;
