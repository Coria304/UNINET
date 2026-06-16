import { NavLink, Outlet } from "react-router-dom";

import NotificationBell from "@/components/NotificationBell";
import { useLogout } from "@/hooks/useAuth";
import { useAuthStore } from "@/stores/authStore";

const NAV = [
  { to: "/portal", label: "Inicio", end: true },
  { to: "/portal/reportar", label: "Reportar falla" },
  { to: "/portal/mis-reportes", label: "Mis reportes" },
  { to: "/portal/speedtest", label: "Speedtest" },
];

function navClass({ isActive }: { isActive: boolean }) {
  return [
    "text-sm transition-colors duration-150 pb-0.5",
    isActive
      ? "text-[#111111] font-medium border-b-2 border-[#111111]"
      : "text-[#787774] hover:text-[#111111] border-b-2 border-transparent",
  ].join(" ");
}

function UsuarioLayout() {
  const usuario = useAuthStore((s) => s.usuario);
  const logoutMutation = useLogout();

  return (
    <div className="min-h-screen flex flex-col bg-[#F7F6F3]">
      <header className="bg-white border-b border-[#EAEAEA] px-6 py-0">
        <div className="flex items-center justify-between gap-6 h-14 max-w-6xl mx-auto">
          <span className="text-sm font-semibold tracking-tight text-[#111111] shrink-0">
            UniNet Connect
          </span>

          <nav className="flex items-center gap-6 h-full">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={navClass}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="flex items-center gap-4 text-sm shrink-0">
            <NotificationBell variant="onLight" />
            <span className="text-[#787774] hidden sm:block">
              {usuario?.nombre_completo}
            </span>
            <button
              type="button"
              onClick={() => logoutMutation.mutate()}
              className="text-[#787774] hover:text-[#111111] transition-colors duration-150"
            >
              Salir
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}

export default UsuarioLayout;
