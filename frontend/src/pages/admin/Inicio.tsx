import { Link } from "react-router-dom";

import { useTicketsList } from "@/hooks/useTickets";
import type { EstadoTicket } from "@/lib/types";

function AdminInicio() {
  const { data: tickets, isLoading } = useTicketsList({}, 60_000);

  const total = tickets?.length ?? 0;
  const countBy = (estado: EstadoTicket) =>
    tickets?.filter((t) => t.estado === estado).length ?? 0;
  const sinAsignar =
    tickets?.filter((t) => !t.asignado_a_id && t.estado !== "resuelto").length ?? 0;

  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-2xl font-semibold">Dashboard administrativo</h2>
        <p className="text-slate-500 text-sm mt-1">
          Resumen del estado actual del sistema de tickets.
        </p>
      </header>

      {isLoading ? (
        <p className="text-slate-500">Cargando métricas…</p>
      ) : (
        <section className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Card label="Total" value={total} color="text-slate-700" />
          <Card label="Activos" value={countBy("activo")} color="text-amber-700" />
          <Card label="En proceso" value={countBy("en_proceso")} color="text-blue-700" />
          <Card label="Resueltos" value={countBy("resuelto")} color="text-emerald-700" />
        </section>
      )}

      {sinAsignar > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-900">
          ⚠️ Hay <strong>{sinAsignar}</strong> ticket(s) abiertos sin técnico asignado.
        </div>
      )}

      <Link to="/admin/tickets" className="inline-block btn-primary">
        Ver todos los tickets →
      </Link>
    </div>
  );
}

function Card({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="bg-white rounded-lg shadow p-5">
      <div className="text-sm text-slate-500">{label}</div>
      <div className={`text-3xl font-semibold mt-1 ${color}`}>{value}</div>
    </div>
  );
}

export default AdminInicio;
