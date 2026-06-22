import "dotenv/config";
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import type { Server } from "http";
import { Hono } from "hono";
import { serve } from "@hono/node-server";
import { WebSocketServer } from "ws";

import type { ReviewEvent } from "./core/models.js";
import { resolveApproval } from "./core/approval.js";
import { runPipeline } from "./main.js";

const __dirname = dirname(fileURLToPath(import.meta.url));

const app = new Hono();

app.get("/", (c) => {
  const html = readFileSync(join(__dirname, "../public/index.html"), "utf-8");
  return c.html(html);
});

let activeWsSend: ((event: ReviewEvent) => void) | null = null;

app.post("/review", async (c) => {
  const { code } = await c.req.json<{ code: string }>();
  const send = (event: ReviewEvent) => activeWsSend?.(event);
  runPipeline(code, send).catch(console.error);
  return c.json({ status: "started" });
});

app.post("/approve", async (c) => {
  const { approved } = await c.req.json<{ approved: boolean }>();
  const hadPending = resolveApproval(approved);
  return c.json({ status: hadPending ? "ok" : "no_pending_review" });
});

const port = Number(process.env.PORT ?? 3000);
const server = serve({ fetch: app.fetch, port }, () => {
  console.log(`Server running on http://localhost:${port}`);
  console.log(`  POST /review   — { "code": "..." }`);
  console.log(`  WS   /ws       — stream of ReviewEvent JSON`);
  console.log(`  POST /approve  — { "approved": true|false }`);
});

const wss = new WebSocketServer({ server: server as Server, path: "/ws" });
wss.on("connection", (ws) => {
  activeWsSend = (event: ReviewEvent) => ws.send(JSON.stringify(event));
  ws.on("close", () => {
    activeWsSend = null;
  });
});

export default app;
