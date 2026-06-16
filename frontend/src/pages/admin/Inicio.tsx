import { Link } from "react-router-dom";

import { useTicketsList } from "@/hooks/useTickets";
import type { EstadoTicket } from "@/lib/types";

const ESTADO_STEPS: { key: EstadoTicket; label: string; color: string }[] = [
  { key: "activo", label: "Sin asignar", color: "bg-amber-400" },
  { key: "en_proceso", label: "En proceso", color: "bg-blue-400" },
  { key: "resuelto", label: "Resueltos", color: "bg-emerald-400" },
];

function AdminInicio() {
  const { data: tickets, isLoading } = useTicketsList({}, 60_000);

  const total = tickets?.length ?? 0;
  const countBy = (estado: EstadoTicket) =>
    tickets?.filter((t) => t.estado === estado).length ?? 0;
  const sinAsignar =
    tickets?.filter((t) => !t.asignado_a_id && t.estado !== "resuelto").length ?? 0;

  const activos = countBy("activo");
  const enProceso = countBy("en_proceso");
  const resueltos = countBy("resuelto");

  return (
    <div className="space-y-6 max-w-5xl">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold">Dashboard administrativo</h2>
          <p className="text-[#787774] text-sm mt-1">
            Resumen del sistema de tickets de ESCOM.
          </p>
        </div>
        <Link to="/admin/tickets" className="btn-primary shrink-0">
          Ver tickets →
        </Link>
      </header>

      {sinAsignar > 0 && (
        <div className="flex items-center gap-3 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-sm text-amber-900">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4 shrink-0 text-amber-500">
            <path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495ZM10 5a.75.75 0 0 1 .75.75v3.5a.75.75 0 0 1-1.5 0v-3.5A.75.75 0 0 1 10 5Zm0 9a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z" clipRule="evenodd" />
          </svg>
          <span>
            <strong>{sinAsignar}</strong> ticket{sinAsignar !== 1 ? "s" : ""} abierto{sinAsignar !== 1 ? "s" : ""} sin técnico asignado.{" "}
            <Link to="/admin/tickets" className="underline hover:no-underline">
              Asignar ahora →
            </Link>
          </span>
        </div>
      )}

      {isLoading ? (
        <div className="h-32 bg-white border border-[#EAEAEA] rounded-xl animate-pulse" />
      ) : (
        <>
          {/* Metric row */}
          <div className="bg-white border border-[#EAEAEA] rounded-xl overflow-hidden">
            <div className="grid grid-cols-4 divide-x divide-[#EAEAEA]">
              <MetricCell label="Total" value={total} />
              <MetricCell label="Sin asignar" value={activos} accent="text-amber-700" />
              <MetricCell label="En proceso" value={enProceso} accent="text-blue-700" />
              <MetricCell label="Resueltos" value={resueltos} accent="text-emerald-700" />
            </div>

            {/* Stacked bar */}
            {total > 0 && (
              <div className="px-5 pb-4 pt-1">
                <div className="h-2 flex rounded-full overflow-hidden gap-px">
                  {ESTADO_STEPS.map(({ key, color }) => {
                    const count = countBy(key);
                    if (count === 0) return null;
                    return (
                      <div
                        key={key}
                        className={`${color} transition-all duration-500`}
                        style={{ flex: count }}
                        title={`${count} ${key}`}
                      />
                    );
                  })}
                </div>
                <div className="flex gap-4 mt-2">
                  {ESTADO_STEPS.map(({ key, label, color }) => (
                    <span key={key} className="flex items-center gap-1.5 text-xs text-[#787774]">
                      <span className={`inline-block h-2 w-2 rounded-sm ${color}`} />
                      {label}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Quick access grid */}
          <div className="grid sm:grid-cols-3 gap-3">
            <QuickLink
              to="/admin/monitoreo"
              title="Monitoreo en vivo"
              desc="Estado de APs y semáforo de saturación"
              icon={<SignalIcon />}
            />
            <QuickLink
              to="/admin/alertas"
              title="Alertas activas"
              desc="Umbrales superados que requieren atención"
              icon={<BellIcon />}
            />
            <QuickLink
              to="/admin/reportes"
              title="Reportes SLA"
              desc="MTTR, tendencias y exportación PDF"
              icon={<ChartIcon />}
            />
          </div>
        </>
      )}
    </div>
  );
}

function MetricCell({ label, value, accent }: { label: string; value: number; accent?: string }) {
  return (
    <div className="px-5 py-4">
      <div className="text-xs text-[#AAAAAA] uppercase tracking-wider mb-1">{label}</div>
      <div className={`text-3xl font-semibold tabular-nums ${accent ?? "text-[#111111]"}`}>{value}</div>
    </div>
  );
}

function QuickLink({ to, title, desc, icon }: { to: string; title: string; desc: string; icon: React.ReactNode }) {
  return (
    <Link
      to={to}
      className="group flex items-start gap-3 bg-white border border-[#EAEAEA] rounded-xl px-4 py-4 hover:border-[#111111] transition-colors"
    >
      <div className="shrink-0 mt-0.5 text-[#787774] group-hover:text-[#111111] transition-colors">
        {icon}
      </div>
      <div className="min-w-0">
        <div className="text-sm font-medium text-[#111111] truncate">{title}</div>
        <div className="text-xs text-[#787774] mt-0.5">{desc}</div>
      </div>
    </Link>
  );
}

function SignalIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
      <path d="M15.312 11.424a5.5 5.5 0 0 1-9.624 0M2.006 8.267a9 9 0 0 1 15.988 0M10 14.75a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Z" />
      <path d="M4.68 10.344A7 7 0 0 1 15.32 10.344" />
    </svg>
  );
}

function BellIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
      <path fillRule="evenodd" d="M10 2a6 6 0 0 0-6 6v2.87L2.293 12.577A1 1 0 0 0 3 14h14a1 1 0 0 0 .707-1.707L16 10.87V8a6 6 0 0 0-6-6ZM8.5 17.5a1.5 1.5 0 0 0 3 0h-3Z" clipRule="evenodd" />
    </svg>
  );
}

function ChartIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
      <path d="M15.5 2A1.5 1.5 0 0 0 14 3.5v13a1.5 1.5 0 0 0 3 0v-13A1.5 1.5 0 0 0 15.5 2ZM9.5 6A1.5 1.5 0 0 0 8 7.5v9A1.5 1.5 0 0 0 11 16.5v-9A1.5 1.5 0 0 0 9.5 6ZM3.5 10A1.5 1.5 0 0 0 2 11.5v5A1.5 1.5 0 0 0 5 16.5v-5A1.5 1.5 0 0 0 3.5 10Z" />
    </svg>
  );
}

export default AdminInicio;
