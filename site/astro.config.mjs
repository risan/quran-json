import { defineConfig } from "astro/config";
import react from "@astrojs/react";
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath } from "node:url";

export default defineConfig({
  site: "https://quran-json.risanb.com",
  base: "/",
  output: "static",
  outDir: fileURLToPath(new URL("../.build/site/", import.meta.url)),
  build: {
    format: "directory",
  },
  integrations: [react()],
  markdown: {
    shikiConfig: {
      themes: { light: "github-light", dark: "github-dark" },
    },
  },
  vite: {
    plugins: [tailwindcss()],
  },
});
