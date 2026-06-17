import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { makeEvent, type ReviewEvent } from "../../src/core/models.js";

describe("makeEvent", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2024-01-01T00:00:00.000Z"));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("returns an event with the correct shape", () => {
    const event = makeEvent("agent.start", "orchestrator", "hello");
    expect(event).toEqual<ReviewEvent>({
      type: "agent.start",
      agent: "orchestrator",
      message: "hello",
      severity: null,
      timestamp: new Date("2024-01-01T00:00:00.000Z").getTime(),
    });
  });

  it("defaults severity to null when omitted", () => {
    const event = makeEvent("finding", "dev", "some finding");
    expect(event.severity).toBeNull();
  });

  it("accepts an explicit severity", () => {
    const event = makeEvent("verdict", "lead", "BLOCKED", "critical");
    expect(event.severity).toBe("critical");
  });

  it("sets timestamp to Date.now() at call time", () => {
    const before = Date.now();
    const event = makeEvent("tool.start", "security", "msg");
    const after = Date.now();
    expect(event.timestamp).toBeGreaterThanOrEqual(before);
    expect(event.timestamp).toBeLessThanOrEqual(after);
  });

  it.each([
    "agent.start",
    "agent.thinking",
    "agent.handoff",
    "tool.start",
    "tool.end",
    "finding",
    "human_approval",
    "verdict",
  ] as const)("accepts event type %s", (type) => {
    const event = makeEvent(type, "perf", "msg");
    expect(event.type).toBe(type);
  });

  it.each([
    "orchestrator",
    "dev",
    "security",
    "perf",
    "lead",
  ] as const)("accepts agent %s", (agent) => {
    const event = makeEvent("finding", agent, "msg");
    expect(event.agent).toBe(agent);
  });
});
