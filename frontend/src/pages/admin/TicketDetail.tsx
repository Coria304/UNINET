import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { isAxiosError } from "axios";

import { useTecnicos } from "@/hooks/useAdmin";
import { useTicket, useUpdateTicket } from "@/hooks/useTickets";
import { useEdificios } from "@/hooks/useUbicaciones";
import type { EstadoTicket } from "@/lib/types";
import { ESTADO_LABEL } from "@/lib/types";
import TicketSummary from "@/pages/tickets/TicketSummary";

const TRANSICIONES: Record<EstadoTicket, EstadoTicket[]> = {
  activo: ["en_proceso", "resuelto"],
  en_proceso: ["resuelto", "activo"],
  resuelto: [],
};

function AdminTicketDetail() {
  const { ticketId } = useParams<{ ticketId: string }>();
  const { data: ticket, isLoading, isError } = useTicket(ticketId, 30_000);
  const { data: edificios } = useEdificios();
  const { data: tecnicos } = useTecnicos();
  const update = useUpdateTicket(ticketId ?? "");

  const [comentario, setComentario] = useState("");
  const [tecnicoId, setTecnicoId] = useState<string>("");

  if (isLoading) return <p className="text-[#787774] text-sm">Cargando…</p>;
  if (isError || !ticket) {
    return (
      <p className="text-red-600 text-sm">
        No se pudo cargar el ticket.{" "}
        <Link to="/admin/tickets" className="underline">
          Volver
        </Link>
      </p>
    );
  }

  const cambiarEstado = (nuevoEstado: EstadoTicket) => {
    update.mutate(
      { estado: nuevoEstado, comentario: comentario.trim() || null },
      { onSuccess: () => setComentario("") },
    );
  };

  const asignar = () => {
    if (!tecnicoId) return;
    update.mutate(
      { asignado_a_id: tecnicoId, comentario: comentario.trim() || null },
      { onSuccess: () => setComentario("") },
    );
  };

  const desasignar = () => {
    update.mutate({ asignado_a_id: null });
  };

  const errorMsg = (() => {
    if (!update.isError) return null;
    if (isAxiosError(update.error)) {
      return (
        (update.error.response?.data as { detail?: string } | undefined)?.detail ??
        "No fue posible actualizar el ticket."
      );
    }
    return "Error inesperado.";
  })();

  const cerrado = ticket.estado === "resuelto";

  return (
    <div className="max-w-3xl space-y-6">
      <Link
        to="/admin/tickets"
        className="inline-flex items-center gap-1 text-sm text-[#787774] hover:text-[#111111] transition-colors"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-3.5 w-3.5">
          <path fillRule="evenodd" d="M9.78 4.22a.75.75 0 0 1 0 1.06L7.06 8l2.72 2.72a.75.75 0 1 1-1.06 1.06L5.47 8.53a.75.75 0 0 1 0-1.06l3.25-3.25a.75.75 0 0 1 1.06 0Z" clipRule="evenodd" />
        </svg>
        Todos los tickets
      </Link>

      <TicketSummary ticket={ticket} edificios={edificios} />

      {!cerrado && (
        <div className="bg-white border border-[#EAEAEA] rounded-xl p-5 space-y-5">
          <h3 className="text-sm font-semibold text-[#111111]">Acciones del administrador</h3>

          {/* Asignación a técnico */}
          <div className="space-y-2">
            <p className="text-xs text-[#AAAAAA] uppercase tracking-wider">Asignar a técnico</p>
            <div className="flex gap-2">
              <select
                className="input-base flex-1"
                value={tecnicoId}
                onChange={(e) => setTecnicoId(e.target.value)}
              >
                <option value="">Seleccionar técnico…</option>
                {tecnicos?.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.nombre_completo}
                  </option>
                ))}
              </select>
              <button
                type="button"
                className="btn-primary shrink-0"
                onClick={asignar}
                disabled={!tecnicoId || update.isPending}
              >
                Asignar
              </button>
            </div>
            {ticket.asignado_a && (
              <div className="flex items-center gap-2 text-xs text-[#787774]">
                <span>Asignado a <strong className="text-[#111111]">{ticket.asignado_a.nombre_completo}</strong></span>
                <button
                  type="button"
                  onClick={desasignar}
                  disabled={update.isPending}
                  className="text-[#787774] hover:text-red-600 underline transition-colors"
                >
                  Quitar
                </button>
              </div>
            )}
          </div>

          {/* Comentario */}
          <div className="space-y-2">
            <p className="text-xs text-[#AAAAAA] uppercase tracking-wider">Comentario</p>
            <textarea
              rows={2}
              className="input-base resize-none"
              placeholder="Opcional — se registrará en el historial"
              value={comentario}
              onChange={(e) => setComentario(e.target.value)}
              maxLength={2000}
            />
          </div>

          {/* Transiciones de estado */}
          {TRANSICIONES[ticket.estado].length > 0 && (
            <div className="space-y-2">
              <p className="text-xs text-[#AAAAAA] uppercase tracking-wider">Cambiar estado</p>
              <div className="flex flex-wrap gap-2">
                {TRANSICIONES[ticket.estado].map((nuevo) => (
                  <button
                    key={nuevo}
                    type="button"
                    className="btn-secondary"
                    onClick={() => cambiarEstado(nuevo)}
                    disabled={update.isPending}
                  >
                    Pasar a {ESTADO_LABEL[nuevo]}
                  </button>
                ))}
              </div>
            </div>
          )}

          {errorMsg && (
            <p className="text-sm text-red-600">{errorMsg}</p>
          )}
        </div>
      )}
    </div>
  );
}

export default AdminTicketDetail;
