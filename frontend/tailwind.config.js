/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          900: "#10161f", // page background (lifted from near-black)
          800: "#19222e", // cards
          700: "#222e3d", // raised surfaces
          600: "#3a4a5e", // borders (brighter for visibility)
          500: "#4a5d73", // hover / stronger borders
        },
      },
    },
  },
  plugins: [],
};
