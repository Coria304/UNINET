import { useMemo, useState } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";

import HeatLayer from "@/components/HeatLayer";
import { useMapaCalor } from "@/hooks/useReportes";

interface Rango {
  label: string;
  days: number;
}

const RANGOS: Rango[] = [
  { label: "Últimos 7 días", days: 7 },
  { label: "Últimos 30 días", days: 30 },
  { label: "Últimos 90 días", days: 90 },
];

// Centroide aproximado de ESCOM-IPN. Se usa como fallback cuando no hay
// puntos para promediar.
const FALLBACK_CENTER: [number, number] = [19.5042, -99.1464];

function isoHaceDias(dias: number): string {
  return new Date(Date.now() - dias * 24 * 3600 * 1000).toISOString();
}

function MapaCalor() {
  const [rangoIdx, setRangoIdx] = useState(1); // default: 30 días
  const rango = RANGOS[rangoIdx];

  const filters = useMemo(
    () => ({ desde: isoHaceDias(rango.days) }),
    [rango],
  );

  const { data, isLoading, isError } = useMapaCalor(filters);

  const center = useMemo<[number, number]>(() => {
    if (!data || data.puntos.length === 0) return FALLBACK_CENTER;
    const lat =
      data.puntos.reduce((acc, p) => acc + p.latitud, 0) / data.puntos.length;
    const lon =
      data.puntos.reduce((acc, p) => acc + p.longitud, 0) / data.puntos.length;
    return [lat, lon];
  }, [data]);

  // Para que el heatmap sea legible incluso con 1-2 puntos, usamos el max
  // observado como referencia (en vez del default de leaflet.heat que asume 1).
  const heatPoints = useMemo<[number, number, number][]>(() => {
    if (!data) return [];
    return data.puntos.map((p) => [p.latitud, p.longitud, p.total]);
  }, [data]);

  const maxIntensity = useMemo(() => {
    if (!data || data.puntos.length === 0) return 1;
    return Math.max(...data.puntos.map((p) => p.total));
  }, [data]);

  return (
    <div className="space-y-4 max-w-6xl">
      <header className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold">Mapa de calor de incidencias</h2>
          <p className="text-sm text-slate-500 mt-1">
            Densidad de tickets por edificio del campus.
          </p>
        </div>
        <div className="flex gap-1 bg-white border border-slate-200 rounded-lg p-0.5">
          {RANGOS.map((r, i) => (
            <button
              key={r.label}
              type="button"
              onClick={() => setRangoIdx(i)}
              className={`px-3 py-1.5 text-sm rounded ${
                i === rangoIdx
                  ? "bg-brand-500 text-white"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
      </header>

      {isLoading && <p className="text-slate-500">Cargando mapa…</p>}
      {isError && (
        <p className="text-red-600">No se pudo cargar el mapa de calor.</p>
      )}

      {data && (
        <>
          <div className="bg-white rounded-lg shadow p-2 h-[520px]">
            <MapContainer
              center={center}
              zoom={17}
              scrollWheelZoom={true}
              style={{ height: "100%", width: "100%", borderRadius: "0.375rem" }}
              // key fuerza re-mount cuando cambia el centro tras cargar data.
              key={`${center[0]},${center[1]}`}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <HeatLayer points={heatPoints} max={maxIntensity} />
              {/* Círculos pequeños con tooltip para ver el conteo exacto. */}
              {data.puntos.map((p) => (
                <CircleMarker
                  key={p.edificio_id}
                  center={[p.latitud, p.longitud]}
                  radius={6}
                  pathOptions={{
                    color: "#1e293b",
                    fillColor: "#1e293b",
                    fillOpacity: 0.6,
                    weight: 1,
                  }}
                >
                  <Popup>
                    <strong>{p.codigo}</strong> — {p.nombre}
                    <br />
                    <span className="text-sm">{p.total} reporte(s)</span>
                  </Popup>
                </CircleMarker>
              ))}
            </MapContainer>
          </div>

          <div className="grid sm:grid-cols-2 gap-4 text-sm">
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-xs text-slate-500 uppercase tracking-wide">
                Total en el rango
              </div>
              <div className="text-2xl font-semibold mt-1">{data.total}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-xs text-slate-500 uppercase tracking-wide mb-2">
                Edificios afectados
              </div>
              {data.puntos.length === 0 ? (
                <p className="text-slate-500">Sin reportes en el rango.</p>
              ) : (
                <ul className="space-y-1">
                  {data.puntos.map((p) => (
                    <li key={p.edificio_id} className="flex justify-between">
                      <span>
                        <strong>{p.codigo}</strong>{" "}
                        <span className="text-slate-500">— {p.nombre}</span>
                      </span>
                      <span className="font-medium tabular-nums">{p.total}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default MapaCalor;
