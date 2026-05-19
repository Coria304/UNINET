/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Paleta institucional ESCOM-IPN (placeholder, ajustar con UI/UX).
        brand: {
          50: "#eef6ff",
          500: "#1d4ed8",
          700: "#1e40af",
          900: "#172554",
        },
        // Colores semáforo del mapa de calor (RF005).
        signal: {
          good: "#16a34a", // verde
          high: "#eab308", // amarillo
          saturated: "#dc2626", // rojo
        },
      },
    },
  },
  plugins: [],
};
