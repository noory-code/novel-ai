/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        paper: "#fafafa",
        sketch: "#6366f1",
        paint: "#f59e0b",
        live: "#10b981",
      },
    },
  },
  plugins: [],
};
