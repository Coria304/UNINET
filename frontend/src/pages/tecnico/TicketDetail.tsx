import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { isAxiosError } from "axios";

import { useTicket, useUpdateTicket } from "@/hooks/useTickets";
import { useEdificios } from "@/hooks/useUbicaciones";
import type { EstadoTicket } from "@/lib/types";
import { ESTADO_LABEL } from "@/lib/types";
import TicketSummary from "@/pages/tickets/TicketSummary";
import { useAuthStore } from "@/stores/authStore";

const TRANSICIONES: Record<EstadoTicket, EstadoTicket[]> = {
  activo: ["en_proceso", "resuelto"],
  en_proceso: ["resuelto", "activo"],
  resuelto: [],
};

function TicketDetail() {
  const { ticketId } = useParams<{ ticketId: string }>();
  const usuario = useAuthStore((s) => s.usuario);
  const { data: ticket, isLoading, isError } = useTicket(ticketId, 30_000);
  const { data: edificios } = useEdificios();
  const update = useUpdateTicket(ticketId ?? "");

  const [comentario, setComentario] = useState("");

  if (isLoading) return <p className="text-slate-500">Cargando…</p>;
  if (isError || !ticket) {
    return (
      <p className="text-red-600">
        No se pudo cargar el ticket.{" "}
        <Link to="/tecnico/tickets" className="underline">
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

  const asignarmelo = () => {
    if (!usuario) return;
    update.mutate({ asignado_a_id: usuario.id });
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

  const yaEsMio = ticket.asignado_a?.id === usuario?.id;
  const cerrado = ticket.estado === "resuelto";

  return (
    <div className="max-w-4xl space-y-6">
      <Link
        to="/tecnico/tickets"
        className="text-sm text-slate-500 hover:underline"
      >
        ← Tickets
      </Link>

      <TicketSummary ticket={ticket} edificios={edificios} />

      {!cerrado && (
        <section className="bg-white rounded-lg shadow p-5 space-y-3">
          <h3 className="font-semibold">Acciones</h3>

          {!yaEsMio && (
            <button
              type="button"
              className="text-sm text-brand-600 underline"
              onClick={asignarmelo}
              disabled={update.isPending}
            >
              Asignármelo
            </button>
          )}

          <textarea
            rows={2}
            className="input-base"
            placeholder="Comentario (opcional, queda en el historial)"
            value={comentario}
            onChange={(e) => setComentario(e.target.value)}
            maxLength={2000}
          />
          <div className="flex flex-wrap gap-2">
            {TRANSICIONES[ticket.estado].map((nuevo) => (
              <button
                key={nuevo}
                type="button"
                className="btn-primary"
                onClick={() => cambiarEstado(nuevo)}
                disabled={update.isPending}
              >
                Pasar a {ESTADO_LABEL[nuevo]}
              </button>
            ))}
          </div>
          {errorMsg && <p className="text-sm text-red-600">{errorMsg}</p>}
        </section>
      )}
    </div>
  );
}

export default TicketDetail;
