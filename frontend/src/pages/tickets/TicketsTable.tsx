import { Link } from "react-router-dom";

import type { Edificio, TicketListItem } from "@/lib/types";
import {
  ESTADO_COLOR,
  ESTADO_LABEL,
  TIPO_FALLA_LABEL,
} from "@/lib/types";

interface Props {
  tickets: TicketListItem[];
  edificios?: Edificio[];
  /** Si se pasa, cada fila se vuelve un Link a `${detailBasePath}/${id}`. */
  detailBasePath?: string;
  /** Mostrar columna "Reportante" (técnico/admin sí, estudiante no). */
  showReportante?: boolean;
  reportantes?: Map<string, string>;
}

function formatFecha(iso: string): string {
  return new Date(iso).toLocaleString("es-MX", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function buildLookup(edificios: Edificio[] | undefined) {
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

function TicketsTable({
  tickets,
  edificios,
  detailBasePath,
  showReportante,
  reportantes,
}: Props) {
  const lookup = buildLookup(edificios);

  if (tickets.length === 0) {
    return (
      <p className="bg-white rounded-lg shadow p-6 text-center text-slate-500">
        No hay tickets que coincidan con el filtro.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto bg-white rounded-lg shadow">
      <table className="min-w-full text-sm">
        <thead className="text-left text-slate-500 border-b border-slate-200">
          <tr>
            <th className="px-4 py-2 font-medium">Tipo</th>
            <th className="px-4 py-2 font-medium">Ubicación</th>
            {showReportante && <th className="px-4 py-2 font-medium">Reportante</th>}
            <th className="px-4 py-2 font-medium">Estado</th>
            <th className="px-4 py-2 font-medium">Fecha</th>
          </tr>
        </thead>
        <tbody>
          {tickets.map((t) => {
            const ubicacion = (
              <>
                <strong>{lookup.edif.get(t.edificio_id) ?? "?"}</strong>
                {t.aula_id && <> · {lookup.aulas.get(t.aula_id) ?? "?"}</>}
              </>
            );
            const RowWrapper = detailBasePath ? "tr" : "tr";
            return (
              <RowWrapper key={t.id} className="border-b border-slate-100 hover:bg-slate-50">
                <td className="px-4 py-2">
                  {detailBasePath ? (
                    <Link
                      to={`${detailBasePath}/${t.id}`}
                      className="text-brand-600 hover:underline"
                    >
                      {TIPO_FALLA_LABEL[t.tipo_falla]}
                    </Link>
                  ) : (
                    TIPO_FALLA_LABEL[t.tipo_falla]
                  )}
                </td>
                <td className="px-4 py-2">{ubicacion}</td>
                {showReportante && (
                  <td className="px-4 py-2 text-slate-600">
                    {reportantes?.get(t.reportante_id) ?? t.reportante_id.slice(0, 8)}
                  </td>
                )}
                <td className="px-4 py-2">
                  <span className={`text-xs px-2 py-0.5 rounded ${ESTADO_COLOR[t.estado]}`}>
                    {ESTADO_LABEL[t.estado]}
                  </span>
                </td>
                <td className="px-4 py-2 text-slate-500 whitespace-nowrap">
                  {formatFecha(t.created_at)}
                </td>
              </RowWrapper>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default TicketsTable;
