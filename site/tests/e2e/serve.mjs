import { createReadStream } from "node:fs";
import { stat } from "node:fs/promises";
import { createServer } from "node:http";
import { extname, join, normalize } from "node:path";

const types = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript",
  ".css": "text/css",
  ".json": "application/json",
  ".svg": "image/svg+xml",
  ".woff2": "font/woff2",
  ".txt": "text/plain",
};

/** A static file server for the assembled tree, standing in for Cloudflare Workers. */
export function serve(root, port = 0) {
  const server = createServer(async (request, response) => {
    const path = normalize(decodeURIComponent(new URL(request.url, "http://x").pathname));
    let file = join(root, path);

    try {
      if ((await stat(file)).isDirectory()) {
        file = join(file, "index.html");
      }

      await stat(file);
    } catch {
      response.writeHead(404).end("not found");

      return;
    }

    response.writeHead(200, {
      "content-type": types[extname(file)] ?? "application/octet-stream",
      "access-control-allow-origin": "*",
    });
    createReadStream(file).pipe(response);
  });

  return new Promise((resolve) => {
    server.listen(port, "127.0.0.1", () => {
      resolve({ server, url: `http://127.0.0.1:${server.address().port}` });
    });
  });
}
