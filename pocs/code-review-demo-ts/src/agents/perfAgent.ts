import { RequirementAgent } from "beeai-framework/agents/requirement/agent";
import { ConditionalRequirement } from "beeai-framework/agents/requirement/requirements/conditional";
import { UnconstrainedMemory } from "beeai-framework/memory/unconstrainedMemory";
import { ThinkTool } from "beeai-framework/tools/think";
import { getLLM } from "../core/backend.js";

export async function createPerfAgent() {
  return new RequirementAgent({
    llm: await getLLM(),
    memory: new UnconstrainedMemory(),
    tools: [new ThinkTool()],
    instructions:
      "You are a performance engineer. Review the submitted code for algorithmic complexity issues, " +
      "inefficient loops, unnecessary re-computation, and N+1 query patterns. " +
      "Return a structured list of findings with severity: CRITICAL, WARNING, or INFO.",
    requirements: [
      new ConditionalRequirement(ThinkTool, { forceAtStep: 1, maxInvocations: 3 }),
    ],
  });
}
