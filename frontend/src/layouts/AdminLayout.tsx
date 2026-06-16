import { NavLink, Outlet } from "react-router-dom";

import NotificationBell from "@/components/NotificationBell";
import { useLogout } from "@/hooks/useAuth";
import { useAuthStore } from "@/stores/authStore";

const NAV = [
  { to: "/admin", label: "Dashboard", end: true },
  { to: "/admin/tickets", label: "Tickets" },
  { to: "/admin/reportes", label: "Reportes SLA" },
  { to: "/admin/mapa-calor", label: "Mapa de calor" },
];

function navClass({ isActive }: { isActive: boolean }) {
  return [
    "block px-3 py-2 rounded text-sm transition-colors duration-150",
    isActive
      ? "bg-white/10 text-white font-medium"
      : "text-white/60 hover:text-white hover:bg-white/5",
  ].join(" ");
}

function AdminLayout() {
  const usuario = useAuthStore((s) => s.usuario);
  const logoutMutation = useLogout();

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-56 bg-[#0D0D0D] flex flex-col shrink-0">
        <div className="px-5 py-5 border-b border-white/[0.06]">
          <span className="text-white text-sm font-semibold tracking-tight">
            UniNet Connect
          </span>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-0.5">
          {NAV.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} className={navClass}>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="px-5 py-4 border-t border-white/[0.06] text-xs">
          <div className="text-white/90 font-medium truncate">
            {usuario?.nombre_completo}
          </div>
          <div className="text-white/40 mt-0.5">Administrador TI</div>
          <button
            type="button"
            onClick={() => logoutMutation.mutate()}
            className="mt-3 text-white/40 hover:text-white/70 transition-colors duration-150 text-xs"
          >
            Cerrar sesión
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 flex flex-col min-w-0 bg-[#F7F6F3]">
        <div className="flex justify-end items-center px-6 py-3 bg-white border-b border-[#EAEAEA]">
          <NotificationBell variant="onLight" />
        </div>
        <div className="flex-1 p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

export default AdminLayout;
