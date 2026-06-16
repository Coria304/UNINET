import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  useDeleteNotificacion,
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
  const deleteOne = useDeleteNotificacion();

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
  const iconColor = isDarkBg ? "text-white" : "text-[#111111]";
  const hoverBg = isDarkBg ? "hover:bg-white/15" : "hover:bg-[#F7F6F3]";
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
        <div className="absolute right-0 mt-2 w-80 max-h-96 overflow-y-auto bg-white text-[#111111] rounded-lg border border-[#EAEAEA] z-50">
          <div className="flex items-center justify-between px-4 py-2 border-b border-[#EAEAEA]">
            <span className="font-semibold text-sm">Notificaciones</span>
            {totalNoLeidas > 0 && (
              <button
                type="button"
                onClick={() => markAll.mutate()}
                className="text-xs text-[#111111] underline hover:no-underline"
                disabled={markAll.isPending}
              >
                Marcar todas como leídas
              </button>
            )}
          </div>
          {items.length === 0 ? (
            <div className="px-4 py-8 text-center">
              <div className="text-2xl mb-2">○</div>
              <p className="text-sm text-[#787774]">Sin notificaciones nuevas.</p>
            </div>
          ) : (
            <ul>
              {items.map((n) => (
                <li key={n.id} className={`group flex items-start border-b border-[#EAEAEA] border-l-2 hover:bg-[#F7F6F3] ${
                  n.leida ? "opacity-60 border-transparent" : "border-[#111111]"
                }`}>
                  <button
                    type="button"
                    onClick={() => handleClickItem(n)}
                    className="flex-1 text-left px-4 py-3 min-w-0"
                  >
                    <div className="text-sm font-medium truncate">{n.titulo}</div>
                    <div className="text-xs text-[#787774] line-clamp-2 mt-0.5">
                      {n.mensaje}
                    </div>
                    <div className="text-[11px] text-[#AAAAAA] mt-1">
                      {fmt(n.created_at)}
                    </div>
                  </button>
                  <button
                    type="button"
                    aria-label="Eliminar notificación"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteOne.mutate(n.id);
                    }}
                    className="shrink-0 p-3 text-[#AAAAAA] hover:text-[#111111] opacity-0 group-hover:opacity-100 transition-opacity duration-150"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-3.5 w-3.5">
                      <path d="M5.28 4.22a.75.75 0 0 0-1.06 1.06L6.94 8l-2.72 2.72a.75.75 0 1 0 1.06 1.06L8 9.06l2.72 2.72a.75.75 0 1 0 1.06-1.06L9.06 8l2.72-2.72a.75.75 0 0 0-1.06-1.06L8 6.94 5.28 4.22Z" />
                    </svg>
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
