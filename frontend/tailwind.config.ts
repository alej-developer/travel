import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      // ─── Color Palette ──────────────────────────────────────────────────
      colors: {
        // Primary — Airbnb-inspired rose-red for CTAs
        primary: {
          50:  "#fff1f2",
          100: "#ffe4e6",
          200: "#fecdd3",
          300: "#fda4af",
          400: "#fb7185",
          500: "#FF385C", // Brand primary
          600: "#e11d48",
          700: "#be123c",
          800: "#9f1239",
          900: "#881337",
          950: "#4c0519",
        },
        // Accent — Teal (secondary brand, airbnb-teal-inspired)
        accent: {
          50:  "#f0fdfa",
          100: "#ccfbf1",
          200: "#99f6e4",
          300: "#5eead4",
          400: "#2dd4bf",
          500: "#00A699", // Accent primary
          600: "#0d9488",
          700: "#0f766e",
          800: "#115e59",
          900: "#134e4a",
          950: "#042f2e",
        },
        // Neutral — cool grays for UI structure
        neutral: {
          0:   "#ffffff",
          25:  "#fafafa",
          50:  "#f7f7f7",
          100: "#ebebeb",
          200: "#dddddd",
          300: "#b0b0b0",
          400: "#717171",
          500: "#484848",
          600: "#222222",
          700: "#1a1a1a",
          800: "#111111",
          900: "#000000",
        },
        // Surface — card and panel backgrounds
        surface: {
          DEFAULT: "#ffffff",
          raised:  "#ffffff",
          overlay: "rgba(0, 0, 0, 0.04)",
        },
      },

      // ─── Typography ─────────────────────────────────────────────────────
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "-apple-system", "sans-serif"],
        display: ["var(--font-inter)", "system-ui", "-apple-system", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
      fontSize: {
        "2xs": ["0.625rem",  { lineHeight: "0.875rem" }],
        xs:   ["0.75rem",   { lineHeight: "1rem" }],
        sm:   ["0.875rem",  { lineHeight: "1.25rem" }],
        base: ["1rem",      { lineHeight: "1.5rem" }],
        lg:   ["1.125rem",  { lineHeight: "1.75rem" }],
        xl:   ["1.25rem",   { lineHeight: "1.75rem" }],
        "2xl":["1.5rem",    { lineHeight: "2rem" }],
        "3xl":["1.875rem",  { lineHeight: "2.25rem" }],
        "4xl":["2.25rem",   { lineHeight: "2.5rem" }],
        "5xl":["3rem",      { lineHeight: "1" }],
        "6xl":["3.75rem",   { lineHeight: "1" }],
        "7xl":["4.5rem",    { lineHeight: "1" }],
      },
      fontWeight: {
        thin:       "100",
        extralight: "200",
        light:      "300",
        normal:     "400",
        medium:     "500",
        semibold:   "600",
        bold:       "700",
        extrabold:  "800",
        black:      "900",
      },
      letterSpacing: {
        tightest: "-0.05em",
        tighter:  "-0.025em",
        tight:    "-0.01em",
        normal:   "0em",
        wide:     "0.025em",
        wider:    "0.05em",
        widest:   "0.1em",
      },

      // ─── Spacing ────────────────────────────────────────────────────────
      spacing: {
        "4.5": "1.125rem",
        "5.5": "1.375rem",
        "13":  "3.25rem",
        "15":  "3.75rem",
        "17":  "4.25rem",
        "18":  "4.5rem",
        "22":  "5.5rem",
        "26":  "6.5rem",
        "30":  "7.5rem",
      },

      // ─── Border Radius ───────────────────────────────────────────────────
      borderRadius: {
        none:  "0",
        sm:    "0.25rem",
        DEFAULT:"0.5rem",
        md:    "0.625rem",
        lg:    "0.75rem",
        xl:    "1rem",
        "2xl": "1.25rem",
        "3xl": "1.5rem",
        pill:  "9999px",
        circle:"50%",
      },

      // ─── Shadows — Airbnb-style layered soft shadows ─────────────────────
      boxShadow: {
        none:    "none",
        xs:      "0 1px 2px rgba(0,0,0,0.06)",
        sm:      "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06)",
        DEFAULT: "0 2px 8px rgba(0,0,0,0.08), 0 1px 3px rgba(0,0,0,0.06)",
        md:      "0 4px 12px rgba(0,0,0,0.08), 0 2px 6px rgba(0,0,0,0.06)",
        lg:      "0 8px 24px rgba(0,0,0,0.08), 0 4px 8px rgba(0,0,0,0.04)",
        xl:      "0 16px 40px rgba(0,0,0,0.10), 0 8px 16px rgba(0,0,0,0.06)",
        "2xl":   "0 24px 64px rgba(0,0,0,0.12), 0 12px 24px rgba(0,0,0,0.08)",
        // Search bar — prominent floating card
        search:  "0 2px 4px rgba(0,0,0,0.08), 0 4px 12px rgba(0,0,0,0.05)",
        "search-hover": "0 2px 4px rgba(0,0,0,0.12), 0 6px 20px rgba(0,0,0,0.10)",
        // Card hover
        "card-hover": "0 6px 20px rgba(0,0,0,0.12), 0 3px 10px rgba(0,0,0,0.08)",
        // Inset
        inner:   "inset 0 2px 4px rgba(0,0,0,0.06)",
      },

      // ─── Animation & Transition ──────────────────────────────────────────
      transitionDuration: {
        "75":  "75ms",
        "100": "100ms",
        "150": "150ms",
        "200": "200ms",
        "300": "300ms",
        "500": "500ms",
        "700": "700ms",
      },
      transitionTimingFunction: {
        "ease-smooth": "cubic-bezier(0.4, 0, 0.2, 1)",
        "ease-spring": "cubic-bezier(0.34, 1.56, 0.64, 1)",
        "ease-in-soft": "cubic-bezier(0.4, 0, 1, 1)",
        "ease-out-soft": "cubic-bezier(0, 0, 0.2, 1)",
      },
      keyframes: {
        shimmer: {
          "0%":   { backgroundPosition: "-1000px 0" },
          "100%": { backgroundPosition: "1000px 0" },
        },
        fadeIn: {
          "0%":   { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        fadeInScale: {
          "0%":   { opacity: "0", transform: "scale(0.95)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        slideDown: {
          "0%":   { opacity: "0", transform: "translateY(-8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulse: {
          "0%, 100%": { opacity: "1" },
          "50%":      { opacity: "0.5" },
        },
        spinSlow: {
          "0%":   { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
      },
      animation: {
        shimmer:      "shimmer 2s infinite linear",
        "fade-in":    "fadeIn 0.3s ease-out forwards",
        "fade-scale": "fadeInScale 0.25s ease-out forwards",
        "slide-down": "slideDown 0.2s ease-out forwards",
        "pulse-slow": "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "spin-slow":  "spinSlow 3s linear infinite",
      },

      // ─── Z-Index scale ───────────────────────────────────────────────────
      zIndex: {
        "0":    "0",
        "10":   "10",
        "20":   "20",
        "30":   "30",
        "40":   "40",
        "50":   "50",
        "modal":"100",
        "toast":"110",
        "tooltip":"120",
      },

      // ─── Grid ────────────────────────────────────────────────────────────
      gridTemplateColumns: {
        "auto-fill-card": "repeat(auto-fill, minmax(280px, 1fr))",
        "auto-fill-sm":   "repeat(auto-fill, minmax(200px, 1fr))",
      },

      // ─── Backdrop Blur ───────────────────────────────────────────────────
      backdropBlur: {
        xs: "2px",
        sm: "4px",
        DEFAULT: "8px",
        md: "12px",
        lg: "16px",
        xl: "24px",
      },
    },
  },
  plugins: [],
};

export default config;
