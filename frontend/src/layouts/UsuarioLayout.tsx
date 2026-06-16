import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";

import CambiarPasswordModal from "@/components/CambiarPasswordModal";
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
      ? "text-brand-600 font-medium border-b-2 border-brand-600"
      : "text-[#64748B] hover:text-brand-600 border-b-2 border-transparent",
  ].join(" ");
}

function UsuarioLayout() {
  const usuario = useAuthStore((s) => s.usuario);
  const logoutMutation = useLogout();
  const [showCambiarPwd, setShowCambiarPwd] = useState(false);

  return (
    <div className="min-h-screen flex flex-col bg-[#F5F8FF]">
      <header className="bg-white border-b border-[#E2E8F0] px-6 py-0">
        <div className="flex items-center justify-between gap-6 h-14 max-w-6xl mx-auto">
          <img
            src="/logo-text.png"
            alt="UniNet Connect"
            className="h-16 w-auto shrink-0"
          />

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
            <span className="text-[#64748B] hidden sm:block">
              {usuario?.nombre_completo}
            </span>
            <button
              type="button"
              onClick={() => setShowCambiarPwd(true)}
              className="text-[#64748B] hover:text-brand-600 transition-colors duration-150 text-sm"
            >
              Contraseña
            </button>
            <button
              type="button"
              onClick={() => logoutMutation.mutate()}
              className="text-[#64748B] hover:text-brand-600 transition-colors duration-150"
            >
              Salir
            </button>
            {showCambiarPwd && <CambiarPasswordModal onClose={() => setShowCambiarPwd(false)} />}
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
