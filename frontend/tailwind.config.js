/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "'Plus Jakarta Sans'",
          "'Helvetica Neue'",
          "system-ui",
          "sans-serif",
        ],
      },
      colors: {
        // Paleta UniNet Connect — azul navy institucional
        brand: {
          50:  "#EFF5FF",  // fondo muy claro
          100: "#DBEAFE",  // superficie clara
          200: "#BFDBFE",  // borde/divisor claro
          300: "#93C5FD",  // acento claro
          500: "#2463AE",  // azul medio (texto links, badges)
          600: "#1A4B8A",  // azul primario (botones, activos)
          700: "#163C72",  // hover primario
          800: "#0F2850",  // dark nav item hover
          900: "#0B1D3D",  // sidebar / nav oscuro
        },
        // Acento dorado del icono
        accent: {
          400: "#F0C040",
          500: "#E8A820",
          600: "#C88A10",
        },
        // Neutros de superficie (se mantienen para compatibilidad con clases hardcoded)
        surface: {
          bg:     "#F5F8FF",  // fondo general (tinte azul muy sutil)
          card:   "#FFFFFF",
          border: "#E2E8F0",
          muted:  "#64748B",
          subtle: "#94A3B8",
        },
        // Estados semáforo para el mapa de calor (RF003)
        signal: {
          good:      "#16a34a",
          high:      "#eab308",
          saturated: "#dc2626",
        },
      },
      boxShadow: {
        card: "0 1px 3px rgba(0,0,0,0.04)",
      },
    },
  },
  plugins: [],
};
