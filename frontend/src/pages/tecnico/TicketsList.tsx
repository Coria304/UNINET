import { useState } from "react";

import { useTicketsList } from "@/hooks/useTickets";
import { useEdificios } from "@/hooks/useUbicaciones";
import type { EstadoTicket } from "@/lib/types";
import { ESTADO_LABEL } from "@/lib/types";
import TicketsTable from "@/pages/tickets/TicketsTable";

function TicketsList() {
  const [estado, setEstado] = useState<EstadoTicket | "">("");
  // Polling 30s: el técnico está mirando la pantalla esperando reportes nuevos.
  const { data: tickets, isLoading } = useTicketsList(
    estado ? { estado } : {},
    30_000,
  );
  const { data: edificios } = useEdificios();

  return (
    <div className="space-y-4">
      <header className="flex items-center justify-between gap-4">
        <h2 className="text-2xl font-semibold">Tickets</h2>
        <div className="flex items-center gap-2 text-sm">
          <label htmlFor="filtro-estado" className="text-[#787774]">
            Estado:
          </label>
          <select
            id="filtro-estado"
            className="input-base !w-auto"
            value={estado}
            onChange={(e) => setEstado(e.target.value as EstadoTicket | "")}
          >
            <option value="">Todos</option>
            {(Object.keys(ESTADO_LABEL) as EstadoTicket[]).map((k) => (
              <option key={k} value={k}>
                {ESTADO_LABEL[k]}
              </option>
            ))}
          </select>
        </div>
      </header>

      {isLoading && <p className="text-[#787774]">Cargando…</p>}

      {tickets && (
        <TicketsTable
          tickets={tickets}
          edificios={edificios}
          detailBasePath="/tecnico/tickets"
          showReportante={false}
        />
      )}
    </div>
  );
}

export default TicketsList;
