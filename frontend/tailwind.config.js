/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          magenta: "#C026D3",
          pink: "#EC2F8B",
          coral: "#FF4D6D",
        },
        charcoal: {
          edge: "#141416",
          center: "#3a3a3f",
          surface: "#1b1b1e",
          elevated: "#232327",
        },
        ink: {
          primary: "#FFFFFF",
          secondary: "#A1A1AA",
          muted: "#71717A",
        },
        semantic: {
          success: "#34D399",
          warning: "#FBBF24",
          danger: "#F43F5E",
          info: "#60A5FA",
        },
        risk: {
          low: "#34D399",
          medium: "#FBBF24",
          high: "#FF4D6D",
        },
        deep: {
          orb: "#3b0d24",
          void: "#12060c",
        },
        cream: "#F7F5F6",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["var(--font-jbmono)", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      borderRadius: {
        xl: "1rem",
        "2xl": "1.25rem",
        "3xl": "1.75rem",
      },
      boxShadow: {
        soft: "0 1px 2px rgba(0,0,0,0.35), 0 8px 32px -12px rgba(0,0,0,0.55)",
        card: "0 0 0 1px rgba(255,255,255,0.06), 0 12px 40px -16px rgba(0,0,0,0.6)",
        "card-hover": "0 0 0 1px rgba(236,47,139,0.35), 0 16px 48px -16px rgba(236,47,139,0.35)",
        glow: "0 0 24px rgba(236,47,139,0.45), 0 0 64px rgba(192,38,211,0.25)",
        "glow-sm": "0 0 12px rgba(236,47,139,0.4)",
      },
      backgroundImage: {
        "brand-gradient": "linear-gradient(135deg, #C026D3 0%, #EC2F8B 50%, #FF4D6D 100%)",
        "brand-gradient-soft": "linear-gradient(135deg, rgba(192,38,211,0.22), rgba(236,47,139,0.16), rgba(255,77,109,0.14))",
        "charcoal-radial": "radial-gradient(120% 90% at 50% 0%, #3a3a3f 0%, #1b1b1e 55%, #141416 100%)",
        "orb-depth": "radial-gradient(circle at 50% 40%, #3b0d24 0%, #12060c 65%)",
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
