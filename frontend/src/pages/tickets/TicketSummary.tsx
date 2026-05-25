import type { Edificio, Ticket } from "@/lib/types";
import {
  ESTADO_COLOR,
  ESTADO_LABEL,
  TIPO_FALLA_LABEL,
  formatAulaLabel,
} from "@/lib/types";

function fmt(iso: string): string {
  return new Date(iso).toLocaleString("es-MX", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

interface Props {
  ticket: Ticket;
  edificios?: Edificio[];
}

/**
 * Bloque de solo lectura compartido entre la vista del técnico
 * (con acciones encima) y la del estudiante (sin acciones).
 */
function TicketSummary({ ticket, edificios }: Props) {
  const edif = edificios?.find((e) => e.id === ticket.edificio_id);
  const aula = edif?.pisos
    .flatMap((p) => p.aulas)
    .find((a) => a.id === ticket.aula_id);

  return (
    <div className="space-y-6">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold">
            {TIPO_FALLA_LABEL[ticket.tipo_falla]}
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Reportado por <strong>{ticket.reportante.nombre_completo}</strong> el{" "}
            {fmt(ticket.created_at)}
          </p>
        </div>
        <span className={`text-sm px-3 py-1 rounded ${ESTADO_COLOR[ticket.estado]}`}>
          {ESTADO_LABEL[ticket.estado]}
        </span>
      </header>

      <section className="bg-white rounded-lg shadow p-5 space-y-3">
        <h3 className="font-semibold">Ubicación</h3>
        <p className="text-sm">
          <strong>{edif?.codigo ?? "?"}</strong> — {edif?.nombre ?? ""}
          {aula && (
            <>
              <br />
              <strong>{formatAulaLabel(aula)}</strong>
            </>
          )}
        </p>
        {ticket.descripcion && (
          <>
            <h3 className="font-semibold pt-3 border-t border-slate-100">
              Descripción
            </h3>
            <p className="text-sm text-slate-700 whitespace-pre-wrap">
              {ticket.descripcion}
            </p>
          </>
        )}
        {ticket.asignado_a && (
          <>
            <h3 className="font-semibold pt-3 border-t border-slate-100">
              Atiende
            </h3>
            <p className="text-sm">{ticket.asignado_a.nombre_completo}</p>
          </>
        )}
      </section>

      <section className="bg-white rounded-lg shadow p-5">
        <h3 className="font-semibold mb-3">Historial</h3>
        <ol className="space-y-3 text-sm">
          {ticket.historico.map((h) => (
            <li key={h.id} className="flex items-start gap-3">
              <span className="text-slate-400 whitespace-nowrap">
                {fmt(h.fecha)}
              </span>
              <div>
                <span className={`text-xs px-2 py-0.5 rounded ${ESTADO_COLOR[h.estado_nuevo]}`}>
                  {h.estado_anterior
                    ? `${ESTADO_LABEL[h.estado_anterior]} → ${ESTADO_LABEL[h.estado_nuevo]}`
                    : ESTADO_LABEL[h.estado_nuevo]}
                </span>
                {h.comentario && (
                  <p className="text-slate-600 mt-1">{h.comentario}</p>
                )}
              </div>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}

export default TicketSummary;
