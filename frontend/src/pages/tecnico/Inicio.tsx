import { Link } from "react-router-dom";

import { useTicketsList } from "@/hooks/useTickets";
import { useAuthStore } from "@/stores/authStore";
import { TIPO_FALLA_LABEL } from "@/lib/types";

function TecnicoInicio() {
  const usuario = useAuthStore((s) => s.usuario);
  const { data: tickets } = useTicketsList();

  const activos = tickets?.filter((t) => t.estado === "activo") ?? [];
  const enProceso = tickets?.filter((t) => t.estado === "en_proceso") ?? [];
  const mios = tickets?.filter(
    (t) => t.asignado_a_id === usuario?.id && t.estado !== "resuelto",
  ) ?? [];

  const totalPendiente = activos.length + enProceso.length;
  const total = tickets?.length ?? 0;
  const resueltos = tickets?.filter((t) => t.estado === "resuelto").length ?? 0;
  const progreso = total > 0 ? Math.round((resueltos / total) * 100) : 0;

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold">Panel de soporte</h2>
          <p className="text-sm text-[#787774] mt-1">
            Bienvenido, {usuario?.nombre_completo?.split(" ")[0]}. Estado actual del campus.
          </p>
        </div>
        <Link to="/tecnico/tickets" className="btn-primary shrink-0">
          Ver tickets →
        </Link>
      </div>

      {/* Main metric — pending work */}
      <div className="bg-brand-900 text-white rounded-2xl px-8 py-6 flex items-center justify-between gap-6">
        <div>
          <div className="text-xs font-medium tracking-widest uppercase text-white/50 mb-1">
            Tickets pendientes
          </div>
          <div className="text-5xl font-semibold tabular-nums">{totalPendiente}</div>
          <div className="text-sm text-white/60 mt-2">
            {activos.length} sin asignar · {enProceso.length} en proceso
          </div>
        </div>
        <NetworkIcon className="w-20 h-auto text-white/20 shrink-0 hidden sm:block" />
      </div>

      {/* Progress bar */}
      {total > 0 && (
        <div className="bg-white border border-[#EAEAEA] rounded-xl px-5 py-4">
          <div className="flex justify-between text-xs text-[#787774] mb-2">
            <span>Progreso general</span>
            <span className="font-medium text-[#111111]">{progreso}% resueltos</span>
          </div>
          <div className="h-2 bg-[#F4F3F0] rounded-full overflow-hidden">
            <div
              className="h-full bg-brand-900 rounded-full transition-all duration-500"
              style={{ width: `${progreso}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-[#AAAAAA] mt-1.5">
            <span>{resueltos} resueltos</span>
            <span>{total} totales</span>
          </div>
        </div>
      )}

      {/* My active tickets */}
      {mios.length > 0 && (
        <div className="bg-white border border-[#EAEAEA] rounded-xl overflow-hidden">
          <div className="px-5 py-3 border-b border-[#EAEAEA] flex items-center justify-between">
            <span className="text-sm font-medium">Mis tickets activos</span>
            <span className="text-xs text-white bg-brand-900 rounded-full px-2 py-0.5 tabular-nums">
              {mios.length}
            </span>
          </div>
          <ul className="divide-y divide-[#EAEAEA]">
            {mios.slice(0, 4).map((t) => (
              <li key={t.id}>
                <Link
                  to={`/tecnico/tickets/${t.id}`}
                  className="flex items-center justify-between px-5 py-3 hover:bg-[#F7F6F3] transition-colors group"
                >
                  <span className="text-sm text-[#111111] truncate">
                    {TIPO_FALLA_LABEL[t.tipo_falla] ?? t.tipo_falla}
                  </span>
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 16 16"
                    fill="currentColor"
                    className="h-3.5 w-3.5 text-[#AAAAAA] group-hover:text-[#111111] transition-colors shrink-0 ml-3"
                  >
                    <path
                      fillRule="evenodd"
                      d="M6.22 4.22a.75.75 0 0 1 1.06 0l3.25 3.25a.75.75 0 0 1 0 1.06l-3.25 3.25a.75.75 0 0 1-1.06-1.06L9.19 8 6.22 5.28a.75.75 0 0 1 0-1.06Z"
                      clipRule="evenodd"
                    />
                  </svg>
                </Link>
              </li>
            ))}
          </ul>
          {mios.length > 4 && (
            <div className="px-5 py-3 border-t border-[#EAEAEA] text-center">
              <Link to="/tecnico/tickets" className="text-xs text-[#787774] underline">
                Ver {mios.length - 4} más →
              </Link>
            </div>
          )}
        </div>
      )}

      {/* Empty state */}
      {mios.length === 0 && totalPendiente === 0 && (
        <div className="bg-white border border-[#EAEAEA] rounded-xl px-6 py-8 text-center text-sm text-[#787774]">
          No hay tickets pendientes. ¡Todo en orden!
        </div>
      )}
    </div>
  );
}

function NetworkIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg" className={className} aria-hidden="true">
      <circle cx="40" cy="40" r="8" fill="currentColor" />
      <circle cx="12" cy="20" r="6" fill="currentColor" />
      <circle cx="68" cy="20" r="6" fill="currentColor" />
      <circle cx="12" cy="60" r="6" fill="currentColor" />
      <circle cx="68" cy="60" r="6" fill="currentColor" />
      <line x1="18" y1="23" x2="32" y2="36" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="62" y1="23" x2="48" y2="36" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="18" y1="57" x2="32" y2="44" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="62" y1="57" x2="48" y2="44" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
}

export default TecnicoInicio;
