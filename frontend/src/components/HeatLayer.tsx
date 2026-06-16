import { useEffect } from "react";
import L from "leaflet";
import "leaflet.heat";
import { useMap } from "react-leaflet";

/**
 * Wrapper sobre L.heatLayer. react-leaflet v4 no trae componente nativo
 * para heatmap, así que enganchamos el layer manualmente usando useMap()
 * y lo limpiamos en el cleanup del efecto.
 */
interface Props {
  /** Cada tupla es [lat, lon, intensidad]. */
  points: [number, number, number][];
  /** Radio del punto en píxeles. */
  radius?: number;
  /** Difuminado en píxeles. */
  blur?: number;
  /** Intensidad considerada "máxima" (full color). */
  max?: number;
}

function HeatLayer({
  points,
  radius = 35,
  blur = 25,
  max,
}: Props) {
  const map = useMap();

  useEffect(() => {
    if (!map) return;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const layer = (L as any).heatLayer(points, {
      radius,
      blur,
      max,
      // Gradiente azul→amarillo→rojo para que se lea de un vistazo.
      gradient: { 0.2: "#1e40af", 0.5: "#fbbf24", 0.8: "#ef4444" },
    });
    layer.addTo(map);

    return () => {
      map.removeLayer(layer);
    };
  }, [map, points, radius, blur, max]);

  return null;
}

export default HeatLayer;
