import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { isAxiosError } from "axios";

import { useTicket, useUpdateTicket } from "@/hooks/useTickets";
import { useEdificios } from "@/hooks/useUbicaciones";
import type { EstadoTicket } from "@/lib/types";
import {
  ESTADO_COLOR,
  ESTADO_LABEL,
  TIPO_FALLA_LABEL,
} from "@/lib/types";
import { useAuthStore } from "@/stores/authStore";

function fmt(iso: string): string {
  return new Date(iso).toLocaleString("es-MX", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

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
        No se pudo cargar el ticket. <Link to="/tecnico/tickets" className="underline">Volver</Link>
      </p>
    );
  }

  const edif = edificios?.find((e) => e.id === ticket.edificio_id);
  const aula = edif?.pisos
    .flatMap((p) => p.aulas)
    .find((a) => a.id === ticket.aula_id);

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

  return (
    <div className="max-w-4xl space-y-6">
      <div>
        <Link to="/tecnico/tickets" className="text-sm text-slate-500 hover:underline">
          ← Tickets
        </Link>
      </div>

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
        <span
          className={`text-sm px-3 py-1 rounded ${ESTADO_COLOR[ticket.estado]}`}
        >
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
              Aula <strong>{aula.codigo}</strong>
            </>
          )}
        </p>
        {ticket.descripcion && (
          <>
            <h3 className="font-semibold pt-3 border-t border-slate-100">Descripción</h3>
            <p className="text-sm text-slate-700 whitespace-pre-wrap">{ticket.descripcion}</p>
          </>
        )}
      </section>

      <section className="bg-white rounded-lg shadow p-5 space-y-3">
        <h3 className="font-semibold">Asignación</h3>
        <div className="flex items-center gap-3">
          <span className="text-sm text-slate-600">
            {ticket.asignado_a
              ? `Asignado a ${ticket.asignado_a.nombre_completo}`
              : "Sin asignar"}
          </span>
          {ticket.asignado_a?.id !== usuario?.id && ticket.estado !== "resuelto" && (
            <button
              type="button"
              className="text-sm text-brand-600 underline"
              onClick={asignarmelo}
              disabled={update.isPending}
            >
              Asignármelo
            </button>
          )}
        </div>
      </section>

      {ticket.estado !== "resuelto" && (
        <section className="bg-white rounded-lg shadow p-5 space-y-3">
          <h3 className="font-semibold">Cambiar estado</h3>
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

      <section className="bg-white rounded-lg shadow p-5">
        <h3 className="font-semibold mb-3">Historial</h3>
        <ol className="space-y-3 text-sm">
          {ticket.historico.map((h) => (
            <li key={h.id} className="flex items-start gap-3">
              <span className="text-slate-400 whitespace-nowrap">{fmt(h.fecha)}</span>
              <div>
                <span
                  className={`text-xs px-2 py-0.5 rounded ${ESTADO_COLOR[h.estado_nuevo]}`}
                >
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

export default TicketDetail;
