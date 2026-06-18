import { test, expect, type Page } from "@playwright/test";

// ── helpers ──────────────────────────────────────────────────────────────────

type ReviewEvent = {
  type: string;
  agent: string;
  message: string;
  severity: string | null;
  timestamp: number;
};

function evt(
  type: string,
  agent: string,
  message: string,
  severity: string | null = null
): ReviewEvent {
  return { type, agent, message, severity, timestamp: Date.now() };
}

/** Push a fake WebSocket message into the page. */
async function ws(page: Page, event: ReviewEvent) {
  await page.evaluate((data) => {
    // The app stores its WS instance on window._ws
    (window as any)._ws?.onmessage?.({ data });
  }, JSON.stringify(event));
}

// ── mock WebSocket so tests don't need a real backend ────────────────────────

const mockWsScript = () => {
  window.WebSocket = class MockWS {
    url: string;
    readyState = 0;
    onopen: ((e: Event) => void) | null = null;
    onclose: ((e: Event) => void) | null = null;
    onerror: ((e: Event) => void) | null = null;
    onmessage: ((e: MessageEvent) => void) | null = null;

    constructor(url: string) {
      this.url = url;
      // Fire onopen asynchronously so the app can assign handlers first.
      Promise.resolve().then(() => {
        this.readyState = 1;
        this.onopen?.({} as Event);
      });
    }

    send() {}
    close() {
      this.readyState = 3;
      this.onclose?.({} as Event);
    }
  } as unknown as typeof WebSocket;
};

test.beforeEach(async ({ page }) => {
  await page.addInitScript(mockWsScript);
  await page.goto("/");
  // Wait for mock onopen to enable the review button.
  await expect(page.locator("#review-btn")).toBeEnabled();
});

// ── page structure ────────────────────────────────────────────────────────────

test.describe("page structure", () => {
  test("renders all five agent nodes in the pipeline", async ({ page }) => {
    for (const agent of ["orchestrator", "dev", "security", "perf", "lead"]) {
      await expect(page.locator(`[data-agent="${agent}"]`)).toBeVisible();
    }
  });

  test("shows empty state before any review is started", async ({ page }) => {
    await expect(page.locator("#empty-state")).toBeVisible();
    await expect(page.locator("#verdict-box")).not.toBeVisible();
    await expect(page.locator("#approval-box")).not.toBeVisible();
  });

  test("WS status shows Connected", async ({ page }) => {
    await expect(page.locator("#ws-label")).toHaveText("Connected");
  });
});

// ── toolbar buttons ───────────────────────────────────────────────────────────

test.describe("toolbar", () => {
  test("Load sample fills textarea with the example code", async ({ page }) => {
    await page.click("#sample-btn");
    const value = await page.inputValue("#code-input");
    expect(value).toContain("authenticate");
    expect(value).toContain("eval(");
  });

  test("Clear button empties the textarea", async ({ page }) => {
    await page.fill("#code-input", "some code");
    await page.click("#clear-btn");
    expect(await page.inputValue("#code-input")).toBe("");
  });
});

// ── review submission ─────────────────────────────────────────────────────────

test.describe("review submission", () => {
  test("clicking Review sends POST /review with the code", async ({ page }) => {
    const bodies: object[] = [];
    page.on("request", (req) => {
      if (req.url().endsWith("/review"))
        bodies.push(JSON.parse(req.postData() ?? "{}"));
    });

    await page.fill("#code-input", "function foo() {}");
    await page.click("#review-btn");

    await expect.poll(() => bodies.length).toBe(1);
    expect(bodies[0]).toMatchObject({ code: "function foo() {}" });
  });

  test("submitting a review clears the previous event log", async ({ page }) => {
    await page.fill("#code-input", "x");
    await page.click("#review-btn");
    await ws(page, evt("agent.start", "orchestrator", "First run"));

    // Complete the review so the button re-enables
    await ws(page, evt("verdict", "lead", "APPROVED", "info"));
    await expect(page.locator("#review-btn")).toBeEnabled();

    // Second submit — log should be wiped
    await page.fill("#code-input", "y");
    await page.click("#review-btn");

    await expect(page.locator(".event-row")).toHaveCount(0);
  });
});

// ── pipeline state ────────────────────────────────────────────────────────────

test.describe("pipeline state", () => {
  test.beforeEach(async ({ page }) => {
    await page.fill("#code-input", "x");
    await page.click("#review-btn");
  });

  test("agent.start makes the agent node active", async ({ page }) => {
    await ws(page, evt("agent.start", "orchestrator", "Starting"));
    await expect(page.locator('[data-agent="orchestrator"]')).toHaveClass(/active/);
  });

  test("any event for an idle agent transitions it to active", async ({ page }) => {
    await ws(page, evt("agent.thinking", "dev", "Thinking about code"));
    await expect(page.locator('[data-agent="dev"]')).toHaveClass(/active/);
  });

  test("lead agent start marks orchestrator and active specialists as done", async ({
    page,
  }) => {
    await ws(page, evt("agent.start", "orchestrator", "Starting"));
    await ws(page, evt("agent.thinking", "dev", "Checking"));
    await ws(page, evt("agent.thinking", "security", "Scanning"));
    await ws(page, evt("agent.start", "lead", "Consolidating"));

    await expect(page.locator('[data-agent="orchestrator"]')).toHaveClass(/done/);
    await expect(page.locator('[data-agent="dev"]')).toHaveClass(/done/);
    await expect(page.locator('[data-agent="security"]')).toHaveClass(/done/);
    await expect(page.locator('[data-agent="lead"]')).toHaveClass(/active/);
  });

  test("verdict marks all agents as done", async ({ page }) => {
    await ws(page, evt("agent.start", "orchestrator", "Starting"));
    await ws(page, evt("agent.start", "lead", "Consolidating"));
    await ws(page, evt("verdict", "lead", "APPROVED", "info"));

    for (const agent of ["orchestrator", "dev", "security", "perf", "lead"]) {
      await expect(page.locator(`[data-agent="${agent}"]`)).toHaveClass(/done/);
    }
  });
});

// ── event log ─────────────────────────────────────────────────────────────────

test.describe("event log", () => {
  test.beforeEach(async ({ page }) => {
    await page.fill("#code-input", "x");
    await page.click("#review-btn");
  });

  test("renders agent and type badges for each event", async ({ page }) => {
    await ws(page, evt("agent.start", "orchestrator", "Starting pipeline"));
    await ws(page, evt("agent.thinking", "dev", "Reviewing style"));
    await ws(page, evt("tool.start", "security", "Using ThinkTool"));

    await expect(page.locator(".badge-orchestrator")).toBeVisible();
    await expect(page.locator(".badge-dev")).toBeVisible();
    await expect(page.locator(".badge-security")).toBeVisible();
  });

  test("agent.start inserts a section divider", async ({ page }) => {
    await ws(page, evt("agent.start", "orchestrator", "Starting"));
    await expect(page.locator(".ev-divider")).toBeVisible();
  });

  test("agent.thinking entry has the dimmed style", async ({ page }) => {
    await ws(page, evt("agent.thinking", "perf", "Analyzing loops"));
    await expect(page.locator(".ev-message.dimmed")).toBeVisible();
  });

  test("long messages get the collapsible class", async ({ page }) => {
    const longMsg = "x".repeat(200);
    await ws(page, evt("agent.thinking", "dev", longMsg));
    await expect(page.locator(".ev-message.collapsible")).toBeVisible();
  });
});

// ── approval flow ─────────────────────────────────────────────────────────────

test.describe("approval flow", () => {
  test.beforeEach(async ({ page }) => {
    await page.fill("#code-input", "x");
    await page.click("#review-btn");
    await ws(page, evt("human_approval", "lead", "Waiting for approval"));
    await expect(page.locator("#approval-box")).toBeVisible();
  });

  test("human_approval event shows the approval box", async ({ page }) => {
    await expect(page.locator("#approve-btn")).toBeVisible();
    await expect(page.locator("#block-btn")).toBeVisible();
  });

  test("Approve sends POST /approve with approved: true and hides the box", async ({
    page,
  }) => {
    const bodies: object[] = [];
    page.on("request", (req) => {
      if (req.url().endsWith("/approve"))
        bodies.push(JSON.parse(req.postData() ?? "{}"));
    });

    await page.click("#approve-btn");

    await expect.poll(() => bodies.length).toBe(1);
    expect(bodies[0]).toEqual({ approved: true });
    await expect(page.locator("#approval-box")).not.toBeVisible();
  });

  test("Block sends POST /approve with approved: false and hides the box", async ({
    page,
  }) => {
    const bodies: object[] = [];
    page.on("request", (req) => {
      if (req.url().endsWith("/approve"))
        bodies.push(JSON.parse(req.postData() ?? "{}"));
    });

    await page.click("#block-btn");

    await expect.poll(() => bodies.length).toBe(1);
    expect(bodies[0]).toEqual({ approved: false });
    await expect(page.locator("#approval-box")).not.toBeVisible();
  });
});

// ── verdict display ───────────────────────────────────────────────────────────

test.describe("verdict display", () => {
  test.beforeEach(async ({ page }) => {
    await page.fill("#code-input", "x");
    await page.click("#review-btn");
  });

  test("critical severity shows BLOCKED label with red styling", async ({
    page,
  }) => {
    await ws(page, evt("verdict", "lead", "VERDICT: BLOCKED — SQL injection", "critical"));

    await expect(page.locator("#verdict-box")).toBeVisible();
    await expect(page.locator("#verdict-box")).toHaveClass(/v-blocked/);
    await expect(page.locator("#verdict-label")).toHaveText("BLOCKED");
  });

  test("info severity shows APPROVED label with green styling", async ({
    page,
  }) => {
    await ws(page, evt("verdict", "lead", "VERDICT: APPROVED — looks good", "info"));

    await expect(page.locator("#verdict-box")).toBeVisible();
    await expect(page.locator("#verdict-box")).toHaveClass(/v-approved/);
    await expect(page.locator("#verdict-label")).toHaveText("APPROVED");
  });

  test("warning severity shows CHANGES REQUESTED label", async ({ page }) => {
    await ws(page, evt("verdict", "lead", "CHANGES_REQUESTED — minor issues", "warning"));

    await expect(page.locator("#verdict-box")).toHaveClass(/v-changes/);
    await expect(page.locator("#verdict-label")).toHaveText("CHANGES REQUESTED");
  });

  test("verdict message is truncated in the verdict bar", async ({ page }) => {
    const longVerdict = "APPROVED — " + "detail ".repeat(50);
    await ws(page, evt("verdict", "lead", longVerdict, "info"));

    const text = await page.locator("#verdict-text").textContent();
    expect(text!.length).toBeLessThanOrEqual(210); // 200 chars + "…"
  });
});
