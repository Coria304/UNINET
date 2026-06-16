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

function TicketSummary({ ticket, edificios }: Props) {
  const edif = edificios?.find((e) => e.id === ticket.edificio_id);
  const aula = edif?.pisos
    .flatMap((p) => p.aulas)
    .find((a) => a.id === ticket.aula_id);

  return (
    <div className="space-y-4">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold text-[#111111]">
            {TIPO_FALLA_LABEL[ticket.tipo_falla]}
          </h2>
          <p className="text-sm text-[#787774] mt-1">
            Reportado por{" "}
            <strong className="text-[#111111]">{ticket.reportante.nombre_completo}</strong>{" "}
            el {fmt(ticket.created_at)}
          </p>
        </div>
        <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${ESTADO_COLOR[ticket.estado]}`}>
          {ESTADO_LABEL[ticket.estado]}
        </span>
      </header>

      <div className="bg-white border border-[#EAEAEA] rounded-xl p-5 space-y-4">
        <div>
          <p className="text-xs text-[#AAAAAA] uppercase tracking-wider mb-1">Ubicación</p>
          <p className="text-sm font-medium text-[#111111]">
            Edificio <strong>{edif?.codigo ?? "?"}</strong>
            {edif?.nombre ? ` — ${edif.nombre}` : ""}
          </p>
          {aula && (
            <p className="text-sm text-[#787774] mt-0.5">{formatAulaLabel(aula)}</p>
          )}
        </div>

        {ticket.descripcion && (
          <div className="border-t border-[#EAEAEA] pt-4">
            <p className="text-xs text-[#AAAAAA] uppercase tracking-wider mb-1">Descripción</p>
            <p className="text-sm text-[#111111] whitespace-pre-wrap leading-relaxed">
              {ticket.descripcion}
            </p>
          </div>
        )}

        {ticket.asignado_a && (
          <div className="border-t border-[#EAEAEA] pt-4">
            <p className="text-xs text-[#AAAAAA] uppercase tracking-wider mb-1">Atiende</p>
            <p className="text-sm font-medium text-[#111111]">{ticket.asignado_a.nombre_completo}</p>
          </div>
        )}
      </div>

      {ticket.historico.length > 0 && (
        <div className="bg-white border border-[#EAEAEA] rounded-xl p-5">
          <p className="text-xs text-[#AAAAAA] uppercase tracking-wider mb-4">Historial</p>
          <ol className="space-y-3">
            {ticket.historico.map((h, i) => (
              <li key={h.id} className="flex items-start gap-3 text-sm">
                <div className="flex flex-col items-center mt-0.5 shrink-0">
                  <div className={`h-2 w-2 rounded-full ${i === 0 ? "bg-[#111111]" : "bg-[#EAEAEA]"}`} />
                  {i < ticket.historico.length - 1 && (
                    <div className="w-px flex-1 bg-[#EAEAEA] mt-1 min-h-[1rem]" />
                  )}
                </div>
                <div className="flex-1 min-w-0 pb-3">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${ESTADO_COLOR[h.estado_nuevo]}`}>
                      {h.estado_anterior
                        ? `${ESTADO_LABEL[h.estado_anterior]} → ${ESTADO_LABEL[h.estado_nuevo]}`
                        : ESTADO_LABEL[h.estado_nuevo]}
                    </span>
                    <span className="text-xs text-[#AAAAAA]">{fmt(h.fecha)}</span>
                  </div>
                  {h.comentario && (
                    <p className="text-[#787774] mt-1 leading-relaxed">{h.comentario}</p>
                  )}
                </div>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}

export default TicketSummary;
