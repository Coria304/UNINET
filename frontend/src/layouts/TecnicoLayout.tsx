import { Link } from "react-router-dom";

import { useLogout } from "@/hooks/useAuth";
import { useAuthStore } from "@/stores/authStore";

interface Props {
  children: React.ReactNode;
}

const NAV = [
  { to: "/tecnico", label: "Mis tickets" },
  { to: "/tecnico/historico", label: "Histórico" },
];

function TecnicoLayout({ children }: Props) {
  const usuario = useAuthStore((s) => s.usuario);
  const logoutMutation = useLogout();

  return (
    <div className="flex min-h-screen">
      <aside className="w-56 bg-slate-800 text-white p-4 flex flex-col">
        <h1 className="text-lg font-semibold mb-6">UniNet · Soporte</h1>
        <nav className="flex-1 space-y-1">
          {NAV.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className="block rounded px-3 py-2 hover:bg-slate-700"
            >
              {item.label}
            </Link>
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
      <main className="flex-1 p-6 bg-slate-50">{children}</main>
    </div>
  );
}

export default TecnicoLayout;
