import { NavLink, Outlet } from "react-router-dom";

import { useLogout } from "@/hooks/useAuth";
import { useAuthStore } from "@/stores/authStore";

const NAV = [
  { to: "/admin", label: "Dashboard", end: true },
  { to: "/admin/tickets", label: "Tickets" },
];

function navClass({ isActive }: { isActive: boolean }) {
  return `block rounded px-3 py-2 hover:bg-brand-700 ${
    isActive ? "bg-brand-700 font-medium" : ""
  }`;
}

function AdminLayout() {
  const usuario = useAuthStore((s) => s.usuario);
  const logoutMutation = useLogout();

  return (
    <div className="flex min-h-screen">
      <aside className="w-60 bg-brand-900 text-white p-4 flex flex-col">
        <h1 className="text-lg font-semibold mb-6">UniNet Connect</h1>
        <nav className="flex-1 space-y-1">
          {NAV.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} className={navClass}>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-6 text-sm">
          <div>{usuario?.nombre_completo}</div>
          <div className="text-brand-50/70">Administrador TI</div>
          <button
            type="button"
            onClick={() => logoutMutation.mutate()}
            className="mt-3 text-brand-50 underline"
          >
            Cerrar sesión
          </button>
        </div>
      </aside>
      <main className="flex-1 p-6 bg-slate-50">
        <Outlet />
      </main>
    </div>
  );
}

export default AdminLayout;
