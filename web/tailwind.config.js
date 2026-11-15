/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#f6f7f5",
        surface: "#ffffff",
        ink: {
          primary: "#14231c",
          secondary: "#4b5b52",
          muted: "#7c8a81",
        },
        brand: {
          DEFAULT: "#1f5c45",
          soft: "#2d7a5c",
          dim: "#e5efe9",
        },
        border: "#dde4df",
        signal: {
          high: "#1f7a4d",
          medium: "#a8710a",
          low: "#b3421f",
          info: "#2563a8",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
