import { RequirementAgent } from "beeai-framework/agents/requirement/agent";
import { ConditionalRequirement } from "beeai-framework/agents/requirement/requirements/conditional";
import { Tool } from "beeai-framework/tools/base";
import { ThinkTool } from "beeai-framework/tools/think";

import { getLLM } from "../core/backend.js";

export async function createSecurityAgent() {
  return new RequirementAgent({
    llm: await getLLM(),
    tools: [new ThinkTool()],
    instructions:
      `You are a security expert. Review the submitted code for SQL injection, eval() misuse, exposed secrets,
      command injection, and unsanitized inputs. Be thorough and conservative — flag anything suspicious. 
      Return a structured list of findings with severity: CRITICAL, WARNING, or INFO.`,
    requirements: [
      new ConditionalRequirement(ThinkTool, { forceAtStep: 1, maxInvocations: 5 }),
      new ConditionalRequirement(ThinkTool, { forceAfter: [Tool], consecutiveAllowed: false }),
    ],
  });
}
