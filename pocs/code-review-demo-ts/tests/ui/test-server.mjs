import http from "http";
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const html = readFileSync(join(__dirname, "../../public/index.html"), "utf-8");

http
  .createServer((req, res) => {
    if (
      req.method === "POST" &&
      (req.url === "/review" || req.url === "/approve")
    ) {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end('{"status":"ok"}');
      return;
    }
    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    res.end(html);
  })
  .listen(4321, () => {
    console.log("UI test server on http://localhost:4321");
  });
