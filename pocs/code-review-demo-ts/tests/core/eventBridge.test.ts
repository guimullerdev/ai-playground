import { describe, it, expect, vi } from "vitest";
import { attachBridge } from "../../src/core/eventBridge.js";
import type { ReviewEvent } from "../../src/core/models.js";

function makeAgentStub() {
  const listeners: Record<string, (data: unknown, meta: { path: string }) => void> = {};
  return {
    emitter: {
      match(pattern: string, cb: (data: unknown, meta: { path: string }) => void) {
        listeners[pattern] = cb;
      },
    },
    emit(path: string, data: unknown) {
      listeners["*.*"]?.(data, { path });
    },
  };
}

function collect(agent: ReturnType<typeof makeAgentStub>, agentName: ReviewEvent["agent"]) {
  const events: ReviewEvent[] = [];
  attachBridge(agent, (e) => events.push(e), agentName);
  return events;
}

describe("attachBridge / mapEvent", () => {
  it("maps a 'think' path to agent.thinking", () => {
    const agent = makeAgentStub();
    const events = collect(agent, "orchestrator");
    agent.emit("agent.think", "thinking...");
    expect(events).toHaveLength(1);
    expect(events[0].type).toBe("agent.thinking");
    expect(events[0].agent).toBe("orchestrator");
  });

  it("maps a 'tool.*start' path to tool.start", () => {
    const agent = makeAgentStub();
    const events = collect(agent, "dev");
    agent.emit("tool.start", "starting tool");
    expect(events[0].type).toBe("tool.start");
  });

  it("maps a 'tool.*end' path to tool.end", () => {
    const agent = makeAgentStub();
    const events = collect(agent, "security");
    agent.emit("tool.end", "done");
    expect(events[0].type).toBe("tool.end");
  });

  it("maps a 'handoff' path to agent.handoff", () => {
    const agent = makeAgentStub();
    const events = collect(agent, "perf");
    agent.emit("handoff.invoke", "passing to security");
    expect(events[0].type).toBe("agent.handoff");
  });

  it("maps a generic 'start' path to agent.start", () => {
    const agent = makeAgentStub();
    const events = collect(agent, "lead");
    agent.emit("agent.start", "beginning");
    expect(events[0].type).toBe("agent.start");
  });

  it("drops unrecognised paths (returns null)", () => {
    const agent = makeAgentStub();
    const events = collect(agent, "orchestrator");
    agent.emit("some.unknown.path", "data");
    expect(events).toHaveLength(0);
  });

  it("extracts text from a string payload", () => {
    const agent = makeAgentStub();
    const events = collect(agent, "dev");
    agent.emit("agent.think", "plain string message");
    expect(events[0].message).toBe("plain string message");
  });

  it("extracts text from object with .text property", () => {
    const agent = makeAgentStub();
    const events = collect(agent, "dev");
    agent.emit("agent.think", { text: "object message" });
    expect(events[0].message).toBe("object message");
  });

  it("extracts text from object with .message property", () => {
    const agent = makeAgentStub();
    const events = collect(agent, "dev");
    agent.emit("agent.think", { message: "msg field" });
    expect(events[0].message).toBe("msg field");
  });

  it("falls back to JSON.stringify for unknown object shapes", () => {
    const agent = makeAgentStub();
    const events = collect(agent, "dev");
    agent.emit("agent.think", { foo: "bar" });
    expect(events[0].message).toBe(JSON.stringify({ foo: "bar" }));
  });

  it("attaches the correct agentName to all events", () => {
    const agent = makeAgentStub();
    const events = collect(agent, "security");
    agent.emit("agent.think", "msg");
    agent.emit("tool.start", "msg");
    for (const e of events) {
      expect(e.agent).toBe("security");
    }
  });
});
