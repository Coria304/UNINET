import { Link } from "react-router-dom";

import { useTicketsList } from "@/hooks/useTickets";
import { useAuthStore } from "@/stores/authStore";

function TecnicoInicio() {
  const usuario = useAuthStore((s) => s.usuario);
  const { data: tickets } = useTicketsList();
  const activos = tickets?.filter((t) => t.estado === "activo").length ?? 0;
  const enProceso = tickets?.filter((t) => t.estado === "en_proceso").length ?? 0;
  const mios =
    tickets?.filter((t) => t.asignado_a_id === usuario?.id && t.estado !== "resuelto").length ?? 0;

  return (
    <div className="space-y-6 max-w-3xl">
      <header>
        <h2 className="text-2xl font-semibold">Panel de soporte</h2>
        <p className="text-slate-500 text-sm mt-1">
          Estado actual de los reportes del campus.
        </p>
      </header>

      <section className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card label="Sin asignar" value={activos} color="text-amber-700" />
        <Card label="En proceso" value={enProceso} color="text-blue-700" />
        <Card label="Mis activos" value={mios} color="text-emerald-700" />
      </section>

      <Link
        to="/tecnico/tickets"
        className="inline-block btn-primary"
      >
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

export default TecnicoInicio;
