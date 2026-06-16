import { useEffect, useMemo, useState } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer, useMap } from "react-leaflet";

import HeatLayer from "@/components/HeatLayer";
import { useMapaCalor } from "@/hooks/useReportes";
import { useEdificios } from "@/hooks/useUbicaciones";

interface Rango {
  label: string;
  days: number;
}

const RANGOS: Rango[] = [
  { label: "Últimos 7 días", days: 7 },
  { label: "Últimos 30 días", days: 30 },
  { label: "Últimos 90 días", days: 90 },
];

const FALLBACK_CENTER: [number, number] = [19.5045, -99.1465];

function isoHaceDias(dias: number): string {
  return new Date(Date.now() - dias * 24 * 3600 * 1000).toISOString();
}

function MapRecenter({ center }: { center: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, map.getZoom(), { animate: true });
  }, [map, center]);
  return null;
}

function MapaCalor() {
  const [rangoIdx, setRangoIdx] = useState(1);
  const [edificioId, setEdificioId] = useState("");
  const rango = RANGOS[rangoIdx];

  const { data: edificios } = useEdificios();

  const filters = useMemo(
    () => ({
      desde: isoHaceDias(rango.days),
      ...(edificioId ? { edificio_id: edificioId } : {}),
    }),
    [rango, edificioId],
  );

  const { data, isLoading, isError, isFetching } = useMapaCalor(filters);

  const center = useMemo<[number, number]>(() => {
    if (!data || data.puntos.length === 0) return FALLBACK_CENTER;
    const lat = data.puntos.reduce((acc, p) => acc + p.latitud, 0) / data.puntos.length;
    const lon = data.puntos.reduce((acc, p) => acc + p.longitud, 0) / data.puntos.length;
    return [lat, lon];
  }, [data]);

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
      <header className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-2xl font-semibold">Mapa de calor de incidencias</h2>
          <p className="text-sm text-[#787774] mt-1">
            Densidad de tickets por edificio del campus.
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <select
            className="input-base !w-auto text-sm"
            value={edificioId}
            onChange={(e) => setEdificioId(e.target.value)}
          >
            <option value="">Todos los edificios</option>
            {edificios?.map((e) => (
              <option key={e.id} value={e.id}>{e.codigo} — {e.nombre}</option>
            ))}
          </select>
          <div className="flex gap-1 bg-white border border-[#EAEAEA] rounded-lg p-0.5">
            {RANGOS.map((r, i) => (
              <button
                key={r.label}
                type="button"
                onClick={() => setRangoIdx(i)}
                className={`px-3 py-1.5 text-sm rounded transition-colors ${
                  i === rangoIdx
                    ? "bg-[#111111] text-white"
                    : "text-[#787774] hover:bg-[#F7F6F3]"
                }`}
              >
                {r.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      {isError && (
        <p className="text-red-600 text-sm">No se pudo cargar el mapa de calor.</p>
      )}

      <div className="relative bg-white rounded-lg border border-[#EAEAEA] p-2 h-[520px]">
        {/* Loading overlay — map stays mounted to avoid tile flicker */}
        {isFetching && !data && (
          <div className="absolute inset-2 z-[400] flex items-center justify-center bg-white/80 rounded">
            <p className="text-sm text-[#787774]">Cargando mapa…</p>
          </div>
        )}
        {isLoading && !data ? null : (
          <MapContainer
            center={center}
            zoom={17}
            scrollWheelZoom={true}
            style={{ height: "100%", width: "100%", borderRadius: "0.375rem" }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <MapRecenter center={center} />
            <HeatLayer points={heatPoints} max={maxIntensity} />
            {data?.puntos.map((p) => (
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
        )}
        {data?.puntos.length === 0 && (
          <div className="absolute inset-2 z-[400] flex items-center justify-center pointer-events-none">
            <div className="bg-white/90 border border-[#EAEAEA] rounded-lg px-4 py-3 text-sm text-[#787774] text-center">
              Sin reportes en el rango seleccionado.
            </div>
          </div>
        )}
      </div>

      {data && (
        <div className="grid sm:grid-cols-2 gap-4 text-sm">
          <div className="bg-white rounded-lg border border-[#EAEAEA] p-4">
            <div className="text-xs text-[#787774] uppercase tracking-wide">
              Total en el rango
            </div>
            <div className="text-2xl font-semibold mt-1">{data.total}</div>
          </div>
          <div className="bg-white rounded-lg border border-[#EAEAEA] p-4">
            <div className="text-xs text-[#787774] uppercase tracking-wide mb-2">
              Edificios afectados
            </div>
            {data.puntos.length === 0 ? (
              <p className="text-[#787774]">Sin reportes en el rango.</p>
            ) : (
              <ul className="space-y-1">
                {data.puntos.map((p) => (
                  <li key={p.edificio_id} className="flex justify-between">
                    <span>
                      <strong>{p.codigo}</strong>{" "}
                      <span className="text-[#787774]">— {p.nombre}</span>
                    </span>
                    <span className="font-medium tabular-nums">{p.total}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default MapaCalor;
