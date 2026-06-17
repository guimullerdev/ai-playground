import { describe, it, expect, vi, beforeEach } from "vitest";

// These are hoisted above imports by Vitest — they run before server.ts loads,
// so serve() and WebSocketServer() never bind to a real port.
vi.mock("@hono/node-server", () => ({
  serve: vi.fn().mockReturnValue({}),
}));

vi.mock("ws", () => ({
  WebSocketServer: vi.fn().mockImplementation(function (this: { on: ReturnType<typeof vi.fn> }) {
    this.on = vi.fn();
  }),
}));

vi.mock("../src/main.js", () => ({
  runPipeline: vi.fn().mockResolvedValue(undefined),
}));

vi.mock("../src/core/approval.js", () => ({
  resolveApproval: vi.fn(),
  waitForApproval: vi.fn(),
}));

import app from "../src/server.js";
import { runPipeline } from "../src/main.js";
import { resolveApproval } from "../src/core/approval.js";

const mockRunPipeline = vi.mocked(runPipeline);
const mockResolveApproval = vi.mocked(resolveApproval);

beforeEach(() => {
  vi.clearAllMocks();
});

describe("POST /review", () => {
  it("returns { status: 'started' }", async () => {
    const res = await app.request("/review", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code: "const x = 1;" }),
    });

    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ status: "started" });
  });

  it("calls runPipeline with the submitted code", async () => {
    await app.request("/review", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code: "function foo() {}" }),
    });

    expect(mockRunPipeline).toHaveBeenCalledOnce();
    expect(mockRunPipeline).toHaveBeenCalledWith("function foo() {}", expect.any(Function));
  });

  it("responds immediately without waiting for runPipeline to finish", async () => {
    let resolveRun!: () => void;
    mockRunPipeline.mockReturnValue(new Promise<void>((r) => (resolveRun = r)));

    const res = await app.request("/review", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code: "slow code" }),
    });

    // Response should arrive before pipeline completes
    expect(res.status).toBe(200);
    resolveRun(); // cleanup
  });
});

describe("POST /approve", () => {
  it("returns { status: 'ok' } when a pending approval exists", async () => {
    mockResolveApproval.mockReturnValue(true);

    const res = await app.request("/approve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ approved: true }),
    });

    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ status: "ok" });
  });

  it("returns { status: 'no_pending_review' } when no approval is pending", async () => {
    mockResolveApproval.mockReturnValue(false);

    const res = await app.request("/approve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ approved: false }),
    });

    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ status: "no_pending_review" });
  });

  it("passes the approved flag to resolveApproval", async () => {
    mockResolveApproval.mockReturnValue(true);

    await app.request("/approve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ approved: false }),
    });

    expect(mockResolveApproval).toHaveBeenCalledWith(false);
  });
});
