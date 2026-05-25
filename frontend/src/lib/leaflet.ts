/**
 * Parche para los íconos por defecto de Leaflet cuando se usa con bundlers
 * (Vite/Webpack). Sin esto los marcadores aparecen rotos porque Leaflet
 * resuelve las URLs de imagen relativas a `marker-icon.png`, que no existen
 * tras el bundle. Tomamos las imágenes del paquete y las inyectamos.
 *
 * Importar una sola vez en main.tsx (`import "@/lib/leaflet"`) basta.
 */
import L from "leaflet";

import iconRetinaUrl from "leaflet/dist/images/marker-icon-2x.png";
import iconUrl from "leaflet/dist/images/marker-icon.png";
import shadowUrl from "leaflet/dist/images/marker-shadow.png";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
delete (L.Icon.Default.prototype as any)._getIconUrl;

L.Icon.Default.mergeOptions({
  iconRetinaUrl,
  iconUrl,
  shadowUrl,
});
