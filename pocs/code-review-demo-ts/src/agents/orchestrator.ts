import { RequirementAgent } from "beeai-framework/agents/requirement/agent";
import { GlobalTrajectoryMiddleware } from "beeai-framework/middleware/trajectory";
import { UnconstrainedMemory } from "beeai-framework/memory/unconstrainedMemory";
import { Tool } from "beeai-framework/tools/base";
import { HandoffTool } from "beeai-framework/tools/handoff";
import { ThinkTool } from "beeai-framework/tools/think";
import { getLLM } from "../core/backend.js";
import { createDevAgent } from "./devAgent.js";
import { createSecurityAgent } from "./securityAgent.js";
import { createPerfAgent } from "./perfAgent.js";

export async function createOrchestrator() {
  const devAgent = await createDevAgent();
  const securityAgent = await createSecurityAgent();
  const perfAgent = await createPerfAgent();

  return {
    orchestrator: new RequirementAgent({
      llm: await getLLM(),
      memory: new UnconstrainedMemory(),
      tools: [
        new ThinkTool(),
        new HandoffTool(devAgent, {
          name: "DevReview",
          description: "Delegate to the Dev agent to review code quality, naming, and patterns.",
        }),
        new HandoffTool(securityAgent, {
          name: "SecurityReview",
          description: "Delegate to the Security agent to review for vulnerabilities and injection risks.",
        }),
        new HandoffTool(perfAgent, {
          name: "PerfReview",
          description: "Delegate to the Performance agent to review for complexity and efficiency issues.",
        }),
      ],
      instructions:
        "You are the code review orchestrator. You MUST delegate the submitted code to ALL THREE specialist agents " +
        "(DevReview, SecurityReview, PerfReview) and collect their findings. " +
        "Once all three have reported back, return a consolidated summary of all findings.",
      middlewares: [new GlobalTrajectoryMiddleware({ included: [Tool] })],
    }),
    devAgent,
    securityAgent,
    perfAgent,
  };
}
