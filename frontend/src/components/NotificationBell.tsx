import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  useMarkAllNotificacionesLeidas,
  useMarkNotificacionLeida,
  useNotificaciones,
} from "@/hooks/useNotificaciones";
import type { Notificacion, Rol } from "@/lib/types";
import { useAuthStore } from "@/stores/authStore";

/**
 * Resuelve a qué ruta navegar cuando el usuario clica una notificación
 * con referencia a un ticket. Cada rol tiene su propio "lugar" donde
 * vive el detalle del ticket.
 */
function ticketRouteFor(rol: Rol | undefined, ticketId: string): string {
  switch (rol) {
    case "personal_tecnico":
      return `/tecnico/tickets/${ticketId}`;
    case "administrador_ti":
      // El admin aún no tiene vista de detalle individual (Sprint 4+);
      // por ahora le llevamos al listado global.
      return "/admin/tickets";
    default:
      return `/portal/mis-reportes/${ticketId}`;
  }
}

function fmt(iso: string): string {
  const d = new Date(iso);
  const diff = (Date.now() - d.getTime()) / 1000;
  if (diff < 60) return "ahora";
  if (diff < 3600) return `hace ${Math.floor(diff / 60)} min`;
  if (diff < 86400) return `hace ${Math.floor(diff / 3600)} h`;
  return d.toLocaleString("es-MX", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

interface Props {
  /**
   * Define el contraste contra el fondo donde vive la campana:
   *  - `onDark`: ícono claro, para barras con bg oscuro (Usuario header azul).
   *  - `onLight`: ícono oscuro, para barras con bg blanco (Admin/Técnico top bar).
   */
  variant?: "onDark" | "onLight";
}

function NotificationBell({ variant = "onDark" }: Props) {
  const usuario = useAuthStore((s) => s.usuario);
  const navigate = useNavigate();
  const { data } = useNotificaciones();
  const markRead = useMarkNotificacionLeida();
  const markAll = useMarkAllNotificacionesLeidas();

  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);

  // Cerrar al hacer click fuera.
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const totalNoLeidas = data?.total_no_leidas ?? 0;
  const items = data?.items ?? [];

  const handleClickItem = (n: Notificacion) => {
    if (!n.leida) markRead.mutate(n.id);
    if (n.entidad_tipo === "ticket" && n.entidad_id) {
      navigate(ticketRouteFor(usuario?.rol, n.entidad_id));
      setOpen(false);
    }
  };

  const isDarkBg = variant === "onDark";
  const iconColor = isDarkBg ? "text-white" : "text-slate-700";
  const hoverBg = isDarkBg ? "hover:bg-white/15" : "hover:bg-slate-100";
  const ringColor = isDarkBg ? "focus:ring-white/30" : "focus:ring-slate-300";

  return (
    <div ref={wrapRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-label="Notificaciones"
        className={`relative p-1.5 rounded ${hoverBg} focus:outline-none focus:ring ${ringColor} ${iconColor}`}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="h-5 w-5"
          aria-hidden="true"
        >
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>
        {totalNoLeidas > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] leading-none min-w-[1.1rem] h-[1.1rem] rounded-full px-1 flex items-center justify-center font-semibold">
            {totalNoLeidas > 9 ? "9+" : totalNoLeidas}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 max-h-96 overflow-y-auto bg-white text-slate-900 rounded-lg shadow-lg ring-1 ring-black/5 z-50">
          <div className="flex items-center justify-between px-4 py-2 border-b border-slate-100">
            <span className="font-semibold text-sm">Notificaciones</span>
            {totalNoLeidas > 0 && (
              <button
                type="button"
                onClick={() => markAll.mutate()}
                className="text-xs text-brand-600 hover:underline"
                disabled={markAll.isPending}
              >
                Marcar todas como leídas
              </button>
            )}
          </div>
          {items.length === 0 ? (
            <p className="px-4 py-6 text-sm text-slate-500 text-center">
              No tienes notificaciones.
            </p>
          ) : (
            <ul>
              {items.map((n) => (
                <li key={n.id}>
                  <button
                    type="button"
                    onClick={() => handleClickItem(n)}
                    className={`w-full text-left px-4 py-3 hover:bg-slate-50 border-b border-slate-100 ${
                      n.leida ? "opacity-60" : ""
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      {!n.leida && (
                        <span className="mt-1.5 h-2 w-2 bg-brand-500 rounded-full flex-shrink-0" />
                      )}
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium truncate">
                          {n.titulo}
                        </div>
                        <div className="text-xs text-slate-600 line-clamp-2 mt-0.5">
                          {n.mensaje}
                        </div>
                        <div className="text-[11px] text-slate-400 mt-1">
                          {fmt(n.created_at)}
                        </div>
                      </div>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

export default NotificationBell;
