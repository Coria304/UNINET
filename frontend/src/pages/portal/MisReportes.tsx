import { Link } from "react-router-dom";

import { useTicketsList } from "@/hooks/useTickets";
import { useEdificios } from "@/hooks/useUbicaciones";
import {
  ESTADO_COLOR,
  ESTADO_LABEL,
  TIPO_FALLA_LABEL,
  formatAulaLabel,
  type Aula,
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
  const aulas = new Map<string, Aula>();
  edificios?.forEach((e) => {
    edif.set(e.id, e.codigo);
    e.pisos.forEach((p) => p.aulas.forEach((a) => aulas.set(a.id, a)));
  });
  return { edif, aulas };
}

function MisReportes() {
  const { data: tickets, isLoading } = useTicketsList();
  const { data: edificios } = useEdificios();
  const lookup = buildUbicacionLookup(edificios);

  if (isLoading) return <p className="text-[#787774]">Cargando reportes…</p>;

  return (
    <div className="space-y-4 max-w-4xl">
      <header className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">Mis reportes</h2>
        <Link to="/portal/reportar" className="text-sm text-brand-600 underline">
          + Crear nuevo
        </Link>
      </header>

      {tickets && tickets.length === 0 && (
        <div className="bg-white rounded-lg border border-[#EAEAEA] p-6 text-center text-[#787774]">
          Aún no has reportado ninguna falla.{" "}
          <Link to="/portal/reportar" className="text-brand-600 underline">
            Reporta la primera
          </Link>
          .
        </div>
      )}

      <ul className="space-y-3">
        {tickets?.map((t) => (
          <li key={t.id}>
            <Link
              to={`/portal/mis-reportes/${t.id}`}
              className="block bg-white rounded-lg border border-[#EAEAEA] p-4 hover:border-[#111111] transition"
            >
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
                  <div className="text-sm text-[#787774]">
                    Edificio{" "}
                    <strong>{lookup.edif.get(t.edificio_id) ?? "?"}</strong>
                    {t.aula_id && lookup.aulas.get(t.aula_id) && (
                      <>
                        {" · "}
                        <strong>{formatAulaLabel(lookup.aulas.get(t.aula_id)!)}</strong>
                      </>
                    )}
                  </div>
                  {t.descripcion && (
                    <p className="text-sm text-[#787774] mt-1 line-clamp-2">
                      {t.descripcion}
                    </p>
                  )}
                </div>
                <div className="text-xs text-[#AAAAAA] whitespace-nowrap text-right">
                  {formatFecha(t.created_at)}
                </div>
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default MisReportes;
