import type { Config } from "tailwindcss";

const config: Config = {
    content: [
        "./app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            backgroundImage: {
                "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
                "gradient-conic":
                    "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
            },
            colors: {
                primary: "#FF4081", // Example vibrant pink
                secondary: "#3F51B5", // Example deep blue
                accent: "#00E676",   // Example vibrant green
            }
        },
    },
    plugins: [],
};
export default config;
