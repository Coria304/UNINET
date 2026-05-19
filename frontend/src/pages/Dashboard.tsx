import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

interface HealthResponse {
  status: string;
  database: string;
}

function Dashboard() {
  const usuario = useAuthStore((s) => s.usuario);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["health"],
    queryFn: async () => (await api.get<HealthResponse>("/health")).data,
    refetchInterval: 30_000,
  });

  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-2xl font-semibold">Bienvenido, {usuario?.nombre_completo}</h2>
        <p className="text-slate-500">Rol: {usuario?.rol}</p>
      </header>

      <section className="bg-white rounded-lg shadow p-4 max-w-md">
        <h3 className="font-medium mb-2">Estado del backend</h3>
        {isLoading && <p>Cargando…</p>}
        {isError && (
          <p className="text-red-600">No se pudo contactar al backend.</p>
        )}
        {data && (
          <ul className="text-sm space-y-1">
            <li>
              API:{" "}
              <span
                className={
                  data.status === "ok" ? "text-green-600" : "text-yellow-600"
                }
              >
                {data.status}
              </span>
            </li>
            <li>
              Base de datos:{" "}
              <span
                className={
                  data.database === "ok" ? "text-green-600" : "text-red-600"
                }
              >
                {data.database}
              </span>
            </li>
          </ul>
        )}
      </section>

      <section className="bg-white rounded-lg shadow p-4">
        <h3 className="font-medium mb-2">Próximos sprints</h3>
        <ol className="list-decimal pl-5 text-sm space-y-1 text-slate-600">
          <li>Sprint 1 — Autenticación con MFA (RF009)</li>
          <li>Sprint 2 — Reporte de fallas y ciclo de tickets (RF001, RF004)</li>
          <li>Sprint 3 — Monitoreo, alertas y mapa de calor (RF002, RF003, RF005, RF007)</li>
        </ol>
      </section>
    </div>
  );
}

export default Dashboard;
