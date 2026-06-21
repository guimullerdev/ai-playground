import { ReviewEvent, makeEvent } from "./models.js";

type WsSend = (event: ReviewEvent) => void;

export function attachBridge(agent: any, send: WsSend, agentName: ReviewEvent["agent"]) {
  agent.emitter.match("*.*", (data: unknown, event: { path: string }) => {
    const mapped = mapEvent(event.path, data, agentName);
    if (mapped) send(mapped);
  });
}

function mapEvent(path: string, data: unknown, agentName: ReviewEvent["agent"]): ReviewEvent | null {
  if (path.includes("think")) {
    return makeEvent("agent.thinking", agentName, extractText(data));
  }
  if (path.includes("tool") && path.includes("start")) {
    return makeEvent("tool.start", agentName, `Using tool: ${path}`);
  }
  if (path.includes("tool") && path.includes("end")) {
    return makeEvent("tool.end", agentName, extractText(data));
  }
  if (path.includes("handoff")) {
    return makeEvent("agent.handoff", agentName, extractText(data));
  }
  if (path.includes("start")) {
    return makeEvent("agent.start", agentName, `Agent ${agentName} started`);
  }
  return null;
}

function extractText(data: unknown): string {
  if (typeof data === "string") return data;
  if (data && typeof data === "object") {
    const d = data as any;
    return d.text ?? d.message ?? d.output ?? JSON.stringify(data);
  }
  return String(data);
}
