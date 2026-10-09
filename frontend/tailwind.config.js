/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#2563EB",
          hover: "#1D4ED8",
          soft: "#3B82F6",
        },
        teal: {
          accent: "#14B8A6",
        },
        navy: {
          DEFAULT: "#0B1A3A",
          deep: "#0A142E",
          elevated: "#0F2350",
        },
        ink: {
          heading: "#0B1A3A",
          body: "#475569",
          muted: "#94A3B8",
        },
        canvas: "#F4F8FF",
        cardborder: "#E6ECF5",
        chartgrid: "#EEF2F7",
        brand: {
          magenta: "#2563EB",
          pink: "#3B82F6",
          coral: "#14B8A6",
        },
        charcoal: {
          edge: "#0A142E",
          center: "#0F2350",
          surface: "#0B1A3A",
          elevated: "#13295C",
        },
        ink2: {
          primary: "#F1F5F9",
          secondary: "#94A3B8",
          muted: "#64748B",
        },
        semantic: {
          success: "#14B8A6",
          warning: "#F59E0B",
          danger: "#EF4444",
          info: "#3B82F6",
        },
        risk: {
          veryHigh: "#EF4444",
          low: "#22C55E",
          medium: "#F59E0B",
          high: "#F97316",
        },
        deep: {
          orb: "#1E3A8A",
          void: "#0A142E",
        },
        cream: "#F4F8FF",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "var(--font-inter)", "Inter", "Plus Jakarta Sans", "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "sans-serif"],
        display: ["var(--font-sans)", "var(--font-inter)", "Inter", "Plus Jakarta Sans", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["var(--font-jbmono)", "JetBrains Mono", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      borderRadius: {
        xl: "1rem",
        "2xl": "1.25rem",
        "3xl": "1.75rem",
      },
      boxShadow: {
        soft: "0 1px 2px rgba(11,26,58,0.06), 0 10px 30px -12px rgba(37,99,235,0.18)",
        card: "0 0 0 1px rgba(230,236,245,1), 0 10px 30px -12px rgba(37,99,235,0.12)",
        "card-hover": "0 0 0 1px rgba(37,99,235,0.35), 0 16px 40px -16px rgba(37,99,235,0.3)",
        glow: "0 0 24px rgba(37,99,235,0.35), 0 0 64px rgba(59,130,246,0.2)",
        "glow-sm": "0 0 12px rgba(37,99,235,0.35)",
      },
      backgroundImage: {
        "brand-gradient": "linear-gradient(135deg, #2563EB 0%, #3B82F6 100%)",
        "brand-gradient-soft": "linear-gradient(135deg, rgba(37,99,235,0.12), rgba(59,130,246,0.08), rgba(20,184,166,0.08))",
        "charcoal-radial": "radial-gradient(120% 90% at 50% 0%, #FFFFFF 0%, #F4F8FF 60%, #EAF0FB 100%)",
        "orb-depth": "radial-gradient(circle at 50% 40%, #1E3A8A 0%, #0A142E 65%)",
        "navy-gradient": "linear-gradient(180deg, #0B1A3A 0%, #0F2350 100%)",
      },
      keyframes: {
        float: { "0%,100%": { transform: "translateY(0px)" }, "50%": { transform: "translateY(-10px)" } },
        "pulse-glow": { "0%,100%": { opacity: "0.55" }, "50%": { opacity: "1" } },
        rise: { from: { opacity: "0", transform: "translateY(10px)" }, to: { opacity: "1", transform: "translateY(0)" } },
        shimmer: { from: { backgroundPosition: "-200% 0" }, to: { backgroundPosition: "200% 0" } },
      },
      animation: {
        float: "float 7s ease-in-out infinite",
        "pulse-glow": "pulse-glow 3.2s ease-in-out infinite",
        rise: "rise 0.35s ease-out both",
        shimmer: "shimmer 1.6s linear infinite",
      },
    },
  },
  plugins: [],
};
