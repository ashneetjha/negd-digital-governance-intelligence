import type { Config } from "tailwindcss";

const config: Config = {
    darkMode: "class",
    content: [
        "./pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./components/**/*.{js,ts,jsx,tsx,mdx}",
        "./app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                // Primary — Government Blue
                primary: {
                    50: "#eff6ff",
                    100: "#dbeafe",
                    200: "#bfdbfe",
                    300: "#93c5fd",
                    400: "#60a5fa",
                    500: "#3b82f6",
                    600: "#1d4ed8",
                    700: "#1e40af",
                    800: "#1e3a8a",
                    900: "#1e3454",
                    950: "#0f1f3c",
                },
                // Neutral with slight warm tint for govt feel
                neutral: {
                    50: "#f8f9fb",
                    100: "#f1f3f6",
                    200: "#e4e8ef",
                    300: "#c9d1dd",
                    400: "#99a6b8",
                    500: "#687690",
                    600: "#4e5a70",
                    700: "#3a4459",
                    800: "#252e40",
                    900: "#151c2c",
                    950: "#0a0f1e",
                },
                // Status colours
                success: "#16a34a",
                warning: "#d97706",
                error: "#dc2626",
                info: "#0284c7",
            },
            fontFamily: {
                sans: ["Inter", "system-ui", "sans-serif"],
                hindi: ["Noto Sans Devanagari", "Inter", "sans-serif"],
                mono: ["JetBrains Mono", "monospace"],
            },
            fontSize: {
                "2xs": ["0.625rem", { lineHeight: "1rem" }],
            },
            borderRadius: {
                "4xl": "2rem",
            },
            boxShadow: {
                card: "0 1px 3px 0 rgb(0 0 0 / 0.07), 0 1px 2px -1px rgb(0 0 0 / 0.05)",
                "card-md": "0 4px 6px -1px rgb(0 0 0 / 0.07), 0 2px 4px -2px rgb(0 0 0 / 0.05)",
                "card-lg": "0 10px 15px -3px rgb(0 0 0 / 0.07), 0 4px 6px -4px rgb(0 0 0 / 0.05)",
            },
            animation: {
                "fade-in": "fadeIn 0.3s ease-in-out",
                "slide-up": "slideUp 0.3s ease-out",
            },
            keyframes: {
                fadeIn: {
                    "0%": { opacity: "0" },
                    "100%": { opacity: "1" },
                },
                slideUp: {
                    "0%": { opacity: "0", transform: "translateY(8px)" },
                    "100%": { opacity: "1", transform: "translateY(0)" },
                },
            },
        },
    },
    plugins: [],
};

export default config;
