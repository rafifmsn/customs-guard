import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        dub: {
          bg: "#ffffff",
          subtle: "#f5f5f5",
          muted: "#fafafa",
          border: "#e5e5e5",
          text: "#111111",
          secondary: "#404040",
          orange: "#ec8434",
          brown: "#793b0b",
          mint: "#86c1a1",
          lavender: "#c095e6",
          plum: "#aa65a0",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "Inter", "system-ui", "sans-serif"],
        display: ["var(--font-satoshi)", "Satoshi", "Inter", "system-ui", "sans-serif"],
        mono: ["var(--font-geist-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
