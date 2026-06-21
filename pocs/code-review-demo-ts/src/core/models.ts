export type EventType =
  | "agent.start"
  | "agent.thinking"
  | "agent.handoff"
  | "tool.start"
  | "tool.end"
  | "finding"
  | "human_approval"
  | "verdict";

export type Severity = "critical" | "warning" | "info" | null;

export interface ReviewEvent {
  type: EventType;
  agent: "orchestrator" | "dev" | "security" | "perf" | "lead";
  message: string;
  severity: Severity;
  timestamp: number;
}

export function makeEvent(
  type: EventType,
  agent: ReviewEvent["agent"],
  message: string,
  severity: Severity = null
): ReviewEvent {
  return { type, agent, message, severity, timestamp: Date.now() };
}
