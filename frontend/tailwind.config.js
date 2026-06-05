/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          900: "#0a0e14",
          800: "#0f1620",
          700: "#161f2c",
          600: "#1e2937",
          500: "#2a3647",
        },
      },
    },
  },
  plugins: [],
};
