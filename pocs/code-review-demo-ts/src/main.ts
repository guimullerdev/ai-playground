import "dotenv/config";
import { makeEvent, type ReviewEvent } from "./core/models.js";
import { attachBridge } from "./core/eventBridge.js";
import { waitForApproval } from "./core/approval.js";
import { createOrchestrator } from "./agents/orchestrator.js";
import { createLeadAgent } from "./agents/leadAgent.js";

export async function runPipeline(
  code: string,
  send: (event: ReviewEvent) => void
) {
  const { orchestrator, devAgent, securityAgent, perfAgent } = await createOrchestrator();
  const leadAgent = await createLeadAgent();

  attachBridge(orchestrator, send, "orchestrator");
  attachBridge(devAgent, send, "dev");
  attachBridge(securityAgent, send, "security");
  attachBridge(perfAgent, send, "perf");
  attachBridge(leadAgent, send, "lead");

  // Step 1: Orchestrator delegates to all three specialist agents
  send(makeEvent("agent.start", "orchestrator", "Starting code review pipeline"));
  const orchestratorResult = await orchestrator.run({
    prompt: `Please review the following code by delegating to all specialist agents (DevReview, SecurityReview, PerfReview):\n\n${code}`,
  });
  const allFindings = orchestratorResult.result.text;

  // Step 2: Human-in-the-loop — pause and wait for /approve
  send(makeEvent("human_approval", "lead", allFindings));
  const approved = await waitForApproval();

  if (!approved) {
    send(makeEvent("verdict", "lead", "VERDICT: BLOCKED (rejected by human reviewer)", "critical"));
    return;
  }

  // Step 3: Lead agent consolidates findings and decides
  send(makeEvent("agent.start", "lead", "Lead agent consolidating findings"));
  const leadResult = await leadAgent.run({
    prompt: `Here are the findings from all specialist agents:\n\n${allFindings}\n\nPlease consolidate and give your verdict.`,
  });

  const verdict = leadResult.result.text;
  const severity = verdict.includes("BLOCKED")
    ? "critical"
    : verdict.includes("CHANGES_REQUESTED")
    ? "warning"
    : "info";

  send(makeEvent("verdict", "lead", verdict, severity));
}
