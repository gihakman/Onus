import type { Config } from "tailwindcss";

/**
 * Onus design language.
 * Editorial, documentation-first, restrained. One accent (evidence green) that
 * signifies a kept commitment, with amber for partial and clay for broken.
 */
const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: "#101317",
          soft: "#2A2F37",
          muted: "#5B626D",
          faint: "#8A909B",
        },
        paper: {
          DEFAULT: "#FAFAF7",
          raised: "#FFFFFF",
          sunken: "#F3F2EC",
        },
        line: {
          DEFAULT: "#E6E4DC",
          strong: "#D6D3C8",
        },
        evidence: {
          DEFAULT: "#12805C",
          soft: "#E4F1EA",
          ink: "#0B4C38",
        },
        partial: {
          DEFAULT: "#B4690E",
          soft: "#F7EDDD",
        },
        broken: {
          DEFAULT: "#B42318",
          soft: "#F7E4E1",
        },
      },
      fontFamily: {
        sans: [
          "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto",
          "Helvetica Neue", "Arial", "sans-serif",
        ],
        serif: [
          "Iowan Old Style", "Palatino Linotype", "Palatino", "Georgia", "serif",
        ],
        mono: [
          "ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace",
        ],
      },
      borderRadius: {
        sm: "6px",
        DEFAULT: "10px",
        lg: "14px",
        xl: "20px",
      },
      boxShadow: {
        card: "0 1px 2px rgba(16,19,23,0.04), 0 8px 24px rgba(16,19,23,0.05)",
        raised: "0 2px 4px rgba(16,19,23,0.05), 0 18px 48px rgba(16,19,23,0.08)",
      },
      maxWidth: {
        prose: "72ch",
      },
      letterSpacing: {
        tightish: "-0.011em",
      },
    },
  },
  plugins: [],
};

export default config;
