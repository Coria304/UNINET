import { Link, Navigate, useParams } from "react-router-dom";

import { useTicket } from "@/hooks/useTickets";
import { useEdificios } from "@/hooks/useUbicaciones";
import TicketSummary from "@/pages/tickets/TicketSummary";
import { useAuthStore } from "@/stores/authStore";

function MiReporteDetalle() {
  const { ticketId } = useParams<{ ticketId: string }>();
  const usuario = useAuthStore((s) => s.usuario);
  // Polling cada 30s para que el estudiante vea avances sin recargar.
  const { data: ticket, isLoading, isError, error } = useTicket(ticketId, 30_000);
  const { data: edificios } = useEdificios();

  if (isLoading) return <p className="text-slate-500">Cargando reporte…</p>;

  // Si el backend devuelve 403/404, mandar a la lista (el ticket no es suyo
  // o no existe).
  if (isError) {
    const status = (error as { response?: { status?: number } } | null)?.response
      ?.status;
    if (status === 403 || status === 404) {
      return <Navigate to="/portal/mis-reportes" replace />;
    }
    return (
      <p className="text-red-600">
        No se pudo cargar el reporte.{" "}
        <Link to="/portal/mis-reportes" className="underline">
          Volver
        </Link>
      </p>
    );
  }

  if (!ticket) return null;

  // Defensa extra: si por alguna razón el ticket pertenece a otro usuario
  // (no debería pasar porque el backend lo bloquea con 403), no lo mostramos.
  if (usuario && ticket.reportante.id !== usuario.id) {
    return <Navigate to="/portal/mis-reportes" replace />;
  }

  return (
    <div className="max-w-3xl space-y-4">
      <Link
        to="/portal/mis-reportes"
        className="text-sm text-slate-500 hover:underline"
      >
        ← Mis reportes
      </Link>
      <TicketSummary ticket={ticket} edificios={edificios} />
    </div>
  );
}

export default MiReporteDetalle;
