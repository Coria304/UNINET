import { Link } from "react-router-dom";

import { useTicketsList } from "@/hooks/useTickets";
import { useAuthStore } from "@/stores/authStore";
import { ESTADO_COLOR, ESTADO_LABEL } from "@/lib/types";

function WifiIcon({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 80 60"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      <path d="M4 26 Q40 -4 76 26" stroke="currentColor" strokeWidth="5" strokeLinecap="round" opacity="0.25" />
      <path d="M14 36 Q40 10 66 36" stroke="currentColor" strokeWidth="5" strokeLinecap="round" opacity="0.5" />
      <path d="M25 46 Q40 28 55 46" stroke="currentColor" strokeWidth="5" strokeLinecap="round" opacity="0.8" />
      <circle cx="40" cy="54" r="5.5" fill="currentColor" />
    </svg>
  );
}

function PortalInicio() {
  const usuario = useAuthStore((s) => s.usuario);
  const { data: tickets } = useTicketsList();

  const total = tickets?.length ?? 0;
  const activos = tickets?.filter((t) => t.estado !== "resuelto").length ?? 0;
  const reciente = tickets?.[0];

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Hero panel */}
      <div className="grid sm:grid-cols-[1fr_auto] gap-0 rounded-2xl overflow-hidden border border-[#EAEAEA] bg-white">
        <div className="px-8 py-8 sm:py-10 flex flex-col justify-center">
          <p className="text-xs font-medium tracking-widest text-[#AAAAAA] uppercase mb-3">
            ESCOM — Campus WiFi
          </p>
          <h2 className="text-3xl font-semibold text-[#111111] leading-tight">
            Hola,{" "}
            <span className="text-[#111111]">
              {usuario?.nombre_completo?.split(" ")[0]}
            </span>
          </h2>
          <p className="text-[#787774] mt-2 text-sm max-w-sm">
            ¿Problemas con la red? Repórtalos en segundos y sigue su estado desde aquí.
          </p>

          <div className="flex flex-wrap gap-3 mt-6">
            <Link to="/portal/reportar" className="btn-primary">
              Reportar falla
            </Link>
            <Link to="/portal/mis-reportes" className="btn-secondary">
              Mis reportes
            </Link>
            <Link to="/portal/speedtest" className="btn-secondary">
              Speedtest
            </Link>
          </div>
        </div>

        <div className="hidden sm:flex items-center justify-center bg-brand-900 px-10 py-8 text-white">
          <WifiIcon className="w-28 h-auto" />
        </div>
      </div>

      {/* Stats strip */}
      {tickets && tickets.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <Stat label="Reportes totales" value={total} />
          <Stat label="En seguimiento" value={activos} highlight={activos > 0} />
          {reciente && (
            <div className="col-span-2 sm:col-span-1 bg-white border border-[#EAEAEA] rounded-xl px-4 py-4">
              <div className="text-xs text-[#AAAAAA] uppercase tracking-wider mb-1">Último reporte</div>
              <div className="text-sm font-medium text-[#111111] truncate">
                {reciente.tipo_falla.replace(/_/g, " ")}
              </div>
              <span className={`mt-1 inline-block text-xs px-2 py-0.5 rounded ${ESTADO_COLOR[reciente.estado]}`}>
                {ESTADO_LABEL[reciente.estado]}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Empty state: no reports yet */}
      {tickets && tickets.length === 0 && (
        <div className="bg-white border border-[#EAEAEA] rounded-xl px-6 py-8 text-center">
          <WifiIcon className="w-16 mx-auto text-[#EAEAEA] mb-3" />
          <p className="text-sm text-[#787774]">
            Aún no tienes reportes. Cuando detectes un problema con la red,{" "}
            <Link to="/portal/reportar" className="text-[#111111] underline">
              repórtalo aquí
            </Link>
            .
          </p>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, highlight }: { label: string; value: number; highlight?: boolean }) {
  return (
    <div className="bg-white border border-[#EAEAEA] rounded-xl px-4 py-4">
      <div className="text-xs text-[#AAAAAA] uppercase tracking-wider mb-1">{label}</div>
      <div className={`text-2xl font-semibold tabular-nums ${highlight ? "text-amber-700" : "text-[#111111]"}`}>
        {value}
      </div>
    </div>
  );
}

export default PortalInicio;
