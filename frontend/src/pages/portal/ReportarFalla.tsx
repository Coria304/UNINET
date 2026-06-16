import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { isAxiosError } from "axios";
import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";

import { useCreateTicket } from "@/hooks/useTickets";
import { useEdificios } from "@/hooks/useUbicaciones";
import type { Edificio, TipoFalla } from "@/lib/types";
import { TIPO_FALLA_LABEL, formatAulaLabel } from "@/lib/types";

// Centroide aproximado de ESCOM-IPN (Zacatenco). Se usa si los edificios
// del seed no traen coordenadas; los seedeados sí las traen.
const FALLBACK_CENTER: [number, number] = [19.504765, -99.146795];

function centroideDe(edificios: Edificio[]): [number, number] {
  const conCoords = edificios.filter(
    (e) => e.latitud !== null && e.longitud !== null,
  );
  if (conCoords.length === 0) return FALLBACK_CENTER;
  const lat = conCoords.reduce((acc, e) => acc + (e.latitud as number), 0) / conCoords.length;
  const lon = conCoords.reduce((acc, e) => acc + (e.longitud as number), 0) / conCoords.length;
  return [lat, lon];
}

function ReportarFalla() {
  const navigate = useNavigate();
  const { data: edificios, isLoading, isError } = useEdificios();
  const create = useCreateTicket();

  const [edificioId, setEdificioId] = useState<string>("");
  const [pisoId, setPisoId] = useState<string>("");
  const [aulaId, setAulaId] = useState<string>("");
  const [tipoFalla, setTipoFalla] = useState<TipoFalla>("sin_senal");
  const [descripcion, setDescripcion] = useState("");

  const edificioSeleccionado = useMemo(
    () => edificios?.find((e) => e.id === edificioId) ?? null,
    [edificios, edificioId],
  );
  const pisoSeleccionado = useMemo(
    () => edificioSeleccionado?.pisos.find((p) => p.id === pisoId) ?? null,
    [edificioSeleccionado, pisoId],
  );

  const center = useMemo(
    () => (edificios ? centroideDe(edificios) : FALLBACK_CENTER),
    [edificios],
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!edificioId) return;
    try {
      await create.mutateAsync({
        edificio_id: edificioId,
        piso_id: pisoId || null,
        aula_id: aulaId || null,
        tipo_falla: tipoFalla,
        descripcion: descripcion.trim() || null,
      });
      navigate("/portal/mis-reportes");
    } catch {
      // El error se renderiza desde mutation.error
    }
  };

  const errorMsg = (() => {
    if (!create.isError) return null;
    if (isAxiosError(create.error)) {
      return (
        (create.error.response?.data as { detail?: string } | undefined)?.detail ??
        "No fue posible crear el reporte."
      );
    }
    return "Error inesperado.";
  })();

  if (isLoading) return <p className="text-slate-500">Cargando edificios…</p>;
  if (isError || !edificios) {
    return (
      <p className="text-red-600">
        No se pudo cargar el catálogo de edificios. Intenta recargar.
      </p>
    );
  }

  return (
    <div className="grid lg:grid-cols-2 gap-6">
      <section className="bg-white rounded-lg shadow p-2 h-[480px]">
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
          {edificios
            .filter((e) => e.latitud !== null && e.longitud !== null)
            .map((e) => (
              <Marker
                key={e.id}
                position={[e.latitud as number, e.longitud as number]}
                eventHandlers={{
                  click: () => {
                    setEdificioId(e.id);
                    setPisoId("");
                    setAulaId("");
                  },
                }}
              >
                <Popup>
                  <strong>{e.codigo}</strong> — {e.nombre}
                  <br />
                  <button
                    type="button"
                    className="text-brand-600 underline mt-1"
                    onClick={() => {
                      setEdificioId(e.id);
                      setPisoId("");
                      setAulaId("");
                    }}
                  >
                    Reportar aquí
                  </button>
                </Popup>
              </Marker>
            ))}
        </MapContainer>
      </section>

      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-5 space-y-4">
        <h2 className="text-lg font-semibold">Detalles del reporte</h2>

        <div>
          <label htmlFor="edificio" className="block text-sm font-medium mb-1">
            Edificio
          </label>
          <select
            id="edificio"
            className="input-base"
            value={edificioId}
            onChange={(e) => {
              setEdificioId(e.target.value);
              setPisoId("");
              setAulaId("");
            }}
            required
          >
            <option value="">— Selecciona en el mapa o aquí —</option>
            {edificios.map((e) => (
              <option key={e.id} value={e.id}>
                {e.codigo} — {e.nombre}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="piso" className="block text-sm font-medium mb-1">
              Piso
            </label>
            <select
              id="piso"
              className="input-base"
              value={pisoId}
              onChange={(e) => {
                setPisoId(e.target.value);
                setAulaId("");
              }}
              disabled={!edificioSeleccionado}
            >
              <option value="">— Opcional —</option>
              {edificioSeleccionado?.pisos.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nombre}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="aula" className="block text-sm font-medium mb-1">
              Aula / Lab
            </label>
            <select
              id="aula"
              className="input-base"
              value={aulaId}
              onChange={(e) => setAulaId(e.target.value)}
              disabled={!pisoSeleccionado}
            >
              <option value="">— Opcional —</option>
              {pisoSeleccionado?.aulas.map((a) => (
                <option key={a.id} value={a.id}>
                  {formatAulaLabel(a)}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label htmlFor="tipo" className="block text-sm font-medium mb-1">
            Tipo de falla
          </label>
          <select
            id="tipo"
            className="input-base"
            value={tipoFalla}
            onChange={(e) => setTipoFalla(e.target.value as TipoFalla)}
            required
          >
            {(Object.keys(TIPO_FALLA_LABEL) as TipoFalla[]).map((k) => (
              <option key={k} value={k}>
                {TIPO_FALLA_LABEL[k]}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="descripcion" className="block text-sm font-medium mb-1">
            Descripción (opcional)
          </label>
          <textarea
            id="descripcion"
            rows={4}
            className="input-base"
            value={descripcion}
            onChange={(e) => setDescripcion(e.target.value)}
            placeholder="Cuéntanos qué pasa: desde cuándo, si afecta a varios, etc."
            maxLength={2000}
          />
        </div>

        {errorMsg && (
          <p role="alert" className="text-sm text-red-600">
            {errorMsg}
          </p>
        )}

        <button
          type="submit"
          className="btn-primary w-full"
          disabled={create.isPending || !edificioId}
        >
          {create.isPending ? "Enviando…" : "Enviar reporte"}
        </button>
      </form>
    </div>
  );
}

export default ReportarFalla;
