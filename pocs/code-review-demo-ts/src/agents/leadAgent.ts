import { RequirementAgent } from "beeai-framework/agents/requirement/agent";
import { ConditionalRequirement } from "beeai-framework/agents/requirement/requirements/conditional";
import { ThinkTool } from "beeai-framework/tools/think";
import { getLLM } from "../core/backend.js";

export async function createLeadAgent() {
  return new RequirementAgent({
    llm: await getLLM(),
    tools: [new ThinkTool()],
    instructions: `You are the lead code reviewer. You will receive consolidated findings from Dev, Security, and Performance agents.
Carefully review all findings and decide on one of: APPROVED | CHANGES_REQUESTED | BLOCKED.
Rules:
- A single CRITICAL security finding → BLOCKED
- Multiple WARNINGs with no CRITICAL → CHANGES_REQUESTED
- Only INFO findings → APPROVED
Always think before deciding. End your response with a line: VERDICT: <decision>`,
    requirements: [
      new ConditionalRequirement(ThinkTool, { forceAtStep: 1 }),
    ],
  });
}
