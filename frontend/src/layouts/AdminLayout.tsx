import { Link } from "react-router-dom";

import { useAuthStore } from "@/stores/authStore";

interface Props {
  children: React.ReactNode;
}

const NAV = [
  { to: "/admin", label: "Dashboard" },
  { to: "/admin/mapa", label: "Mapa de calor" },
  { to: "/admin/tickets", label: "Tickets" },
  { to: "/admin/alertas", label: "Alertas" },
  { to: "/admin/reportes", label: "Reportes SLA" },
  { to: "/admin/configuracion", label: "Configuración" },
];

function AdminLayout({ children }: Props) {
  const usuario = useAuthStore((s) => s.usuario);
  const logout = useAuthStore((s) => s.logout);

  return (
    <div className="flex min-h-screen">
      <aside className="w-60 bg-brand-900 text-white p-4 flex flex-col">
        <h1 className="text-lg font-semibold mb-6">UniNet Connect</h1>
        <nav className="flex-1 space-y-1">
          {NAV.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className="block rounded px-3 py-2 hover:bg-brand-700"
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="mt-6 text-sm">
          <div>{usuario?.nombre_completo}</div>
          <div className="text-brand-50/70">Administrador TI</div>
          <button
            type="button"
            onClick={logout}
            className="mt-3 text-brand-50 underline"
          >
            Cerrar sesión
          </button>
        </div>
      </aside>
      <main className="flex-1 p-6 bg-slate-50">{children}</main>
    </div>
  );
}

export default AdminLayout;
