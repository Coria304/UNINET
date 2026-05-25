import { Link } from "react-router-dom";

import { useAuthStore } from "@/stores/authStore";

function PortalInicio() {
  const usuario = useAuthStore((s) => s.usuario);

  return (
    <div className="space-y-6 max-w-3xl">
      <header>
        <h2 className="text-2xl font-semibold">Hola, {usuario?.nombre_completo}</h2>
        <p className="text-slate-500 text-sm mt-1">
          ¿Tienes problemas con el WiFi en el campus? Repórtalo en un par de clics.
        </p>
      </header>

      <section className="grid sm:grid-cols-2 gap-4">
        <Link
          to="/portal/reportar"
          className="bg-white border border-slate-200 rounded-lg p-5 hover:border-brand-500 transition"
        >
          <h3 className="font-semibold text-brand-700">Reportar una falla</h3>
          <p className="text-sm text-slate-500 mt-1">
            Elige el edificio en el mapa y describe el problema.
          </p>
        </Link>

        <Link
          to="/portal/mis-reportes"
          className="bg-white border border-slate-200 rounded-lg p-5 hover:border-brand-500 transition"
        >
          <h3 className="font-semibold text-brand-700">Mis reportes</h3>
          <p className="text-sm text-slate-500 mt-1">
            Sigue el estado de las fallas que reportaste.
          </p>
        </Link>
      </section>
    </div>
  );
}

export default PortalInicio;
