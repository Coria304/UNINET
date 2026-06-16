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
        // Paleta monocromática cálida — minimalist-ui
        brand: {
          50:  "#F9F9F8",  // superficie cálida (texto claro sobre oscuro)
          100: "#F4F3F0",  // fondo cálido
          200: "#EAEAEA",  // borde/divisor
          500: "#111111",  // acción primaria
          600: "#2A2A2A",  // hover sobre fondo oscuro
          700: "#1A1A1A",  // hover sobre botón
          900: "#0D0D0D",  // sidebar / nav oscuro
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
