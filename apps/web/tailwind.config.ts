import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Primary - Deep emerald tones
        primary: {
          50: "#ecfdf5",
          100: "#d1fae5",
          200: "#a7f3d0",
          300: "#6ee7b7",
          400: "#34d399",
          500: "#10b981",
          600: "#059669",
          700: "#047857",
          800: "#065f46",
          900: "#064e3b",
          950: "#022c22",
        },
        // Accent - Warm gold/amber for contrast
        accent: {
          50: "#fffbeb",
          100: "#fef3c7",
          200: "#fde68a",
          300: "#fcd34d",
          400: "#fbbf24",
          500: "#f59e0b",
          600: "#d97706",
          700: "#b45309",
          800: "#92400e",
          900: "#78350f",
        },
        // Pitch - Dark greens for backgrounds
        pitch: {
          50: "#f0fdf4",
          100: "#dcfce7",
          200: "#bbf7d0",
          300: "#86efac",
          400: "#4ade80",
          500: "#22c55e",
          600: "#16a34a",
          700: "#15803d",
          800: "#166534",
          900: "#14532d",
          950: "#052e16",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      backgroundImage: {
        // Main gradient - Stadium at golden hour
        "pitch-gradient": "linear-gradient(135deg, #064e3b 0%, #065f46 25%, #047857 50%, #0d9488 100%)",
        // Dark gradient for headers
        "pitch-dark": "linear-gradient(135deg, #022c22 0%, #064e3b 50%, #0f766e 100%)",
        // Vibrant gradient for buttons/accents
        "pitch-vibrant": "linear-gradient(135deg, #059669 0%, #10b981 50%, #14b8a6 100%)",
        // Subtle gradient for cards
        "pitch-subtle": "linear-gradient(180deg, #f0fdfa 0%, #ccfbf1 100%)",
        // Gold accent gradient
        "gold-gradient": "linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)",
      },
      boxShadow: {
        "glow-primary": "0 0 20px rgba(16, 185, 129, 0.3)",
        "glow-accent": "0 0 20px rgba(251, 191, 36, 0.3)",
      },
    },
  },
  plugins: [],
} satisfies Config;
