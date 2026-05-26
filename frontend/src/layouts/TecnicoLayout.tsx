import { NavLink, Outlet } from "react-router-dom";

import NotificationBell from "@/components/NotificationBell";
import { useLogout } from "@/hooks/useAuth";
import { useAuthStore } from "@/stores/authStore";

const NAV = [
  { to: "/tecnico", label: "Inicio", end: true },
  { to: "/tecnico/tickets", label: "Tickets" },
];

function navClass({ isActive }: { isActive: boolean }) {
  return `block rounded px-3 py-2 hover:bg-slate-700 ${
    isActive ? "bg-slate-700 font-medium" : ""
  }`;
}

function TecnicoLayout() {
  const usuario = useAuthStore((s) => s.usuario);
  const logoutMutation = useLogout();

  return (
    <div className="flex min-h-screen">
      <aside className="w-56 bg-slate-800 text-white p-4 flex flex-col">
        <h1 className="text-lg font-semibold mb-6">UniNet · Soporte</h1>
        <nav className="flex-1 space-y-1">
          {NAV.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} className={navClass}>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-6 text-sm">
          <div>{usuario?.nombre_completo}</div>
          <div className="text-slate-300">Personal Técnico</div>
          <button
            type="button"
            onClick={() => logoutMutation.mutate()}
            className="mt-3 underline"
          >
            Cerrar sesión
          </button>
        </div>
      </aside>
      <main className="flex-1 bg-slate-50">
        <div className="flex justify-end px-6 py-2 border-b border-slate-200 bg-white">
          <NotificationBell variant="onLight" />
        </div>
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

export default TecnicoLayout;
