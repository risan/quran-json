import { createReadStream, existsSync, statSync } from "node:fs";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "astro/config";
import react from "@astrojs/react";
import tailwindcss from "@tailwindcss/vite";

const DATA_PATHS = [
  "/manifest.json",
  "/chapters.json",
  "/text/",
  "/translations/",
  "/transliteration/",
  "/audio/",
  "/meta/",
];

const dataRoot = normalize(
  process.env.QURAN_JSON_SITE_DATA ?? fileURLToPath(new URL("../.build/data/", import.meta.url)),
);

/** Dev only: serve the built data tree next to the pages, the way the assembled site does. */
function serveData() {
  return {
    name: "quran-json-dev-data",
    apply: "serve",
    configureServer(server) {
      server.middlewares.use((request, response, next) => {
        const path = decodeURIComponent((request.url ?? "").split("?")[0]);

        if (!DATA_PATHS.some((prefix) => path === prefix || path.startsWith(prefix))) {
          next();

          return;
        }

        const file = normalize(join(dataRoot, path));

        if (!file.startsWith(dataRoot) || !existsSync(file) || !statSync(file).isFile()) {
          next();

          return;
        }

        response.setHeader(
          "Content-Type",
          extname(file) === ".json" ? "application/json" : "application/octet-stream",
        );
        createReadStream(file).pipe(response);
      });
    },
  };
}

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
    plugins: [tailwindcss(), serveData()],
  },
});
