import { NavLink, Outlet } from "react-router-dom";

import { useLogout } from "@/hooks/useAuth";
import { useAuthStore } from "@/stores/authStore";

const NAV = [
  { to: "/portal", label: "Inicio", end: true },
  { to: "/portal/reportar", label: "Reportar falla" },
  { to: "/portal/mis-reportes", label: "Mis reportes" },
];

function navClass({ isActive }: { isActive: boolean }) {
  return `hover:underline ${isActive ? "underline font-medium" : ""}`;
}

function UsuarioLayout() {
  const usuario = useAuthStore((s) => s.usuario);
  const logoutMutation = useLogout();

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-brand-500 text-white px-6 py-3 flex items-center justify-between">
        <h1 className="text-lg font-semibold">UniNet Connect</h1>
        <nav className="space-x-4">
          {NAV.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} className={navClass}>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="text-sm">
          <span className="mr-3">{usuario?.nombre_completo}</span>
          <button
            type="button"
            onClick={() => logoutMutation.mutate()}
            className="underline"
          >
            Salir
          </button>
        </div>
      </header>
      <main className="flex-1 p-6 bg-slate-50">
        <Outlet />
      </main>
    </div>
  );
}

export default UsuarioLayout;
