import { Link } from "react-router-dom";

import { useLogout } from "@/hooks/useAuth";
import { useAuthStore } from "@/stores/authStore";

interface Props {
  children: React.ReactNode;
}

const NAV = [
  { to: "/portal", label: "Inicio" },
  { to: "/portal/reportar", label: "Reportar falla" },
  { to: "/portal/mis-tickets", label: "Mis reportes" },
  { to: "/portal/speedtest", label: "Speedtest" },
  { to: "/portal/mapa", label: "Mapa de calor" },
];

function UsuarioLayout({ children }: Props) {
  const usuario = useAuthStore((s) => s.usuario);
  const logoutMutation = useLogout();

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-brand-500 text-white px-6 py-3 flex items-center justify-between">
        <h1 className="text-lg font-semibold">UniNet Connect</h1>
        <nav className="space-x-4">
          {NAV.map((item) => (
            <Link key={item.to} to={item.to} className="hover:underline">
              {item.label}
            </Link>
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
      <main className="flex-1 p-6 bg-slate-50">{children}</main>
    </div>
  );
}

export default UsuarioLayout;
