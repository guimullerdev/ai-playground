import { RequirementAgent } from "beeai-framework/agents/requirement/agent";
import { ConditionalRequirement } from "beeai-framework/agents/requirement/requirements/conditional";
import { ThinkTool } from "beeai-framework/tools/think";

import { getLLM } from "../core/backend.js";

export async function createDevAgent() {
  return new RequirementAgent({
    llm: await getLLM(),
    tools: [new ThinkTool()],
    instructions:
      `You are a senior developer. Review the submitted code for naming conventions, readability, code patterns, and duplication. 
      Return a structured list of findings with severity: CRITICAL, WARNING, or INFO.`,
    requirements: [
      new ConditionalRequirement(ThinkTool, { forceAtStep: 1, maxInvocations: 3 }),
    ],
  });
}
