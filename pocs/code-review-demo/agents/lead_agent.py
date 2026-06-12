import asyncio
from beeai_framework.agents.experimental import RequirementAgent
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.tools.think import ThinkTool
from core.backend import get_llm
from core.models import ReviewEvent


def create_lead_agent() -> RequirementAgent:
    return RequirementAgent(
        llm=get_llm(),
        memory=UnconstrainedMemory(),
        tools=[ThinkTool()],
        role="lead_reviewer",
        instructions=(
            "You are the lead engineer consolidating a code review. "
            "You will receive findings from the dev, security, and performance agents. "
            "Summarize all findings and issue a final verdict: APPROVED, CHANGES_REQUESTED, or BLOCKED. "
            "BLOCKED is required if any critical security issue was found."
        ),
    )


async def run_lead_with_approval(
    lead_agent,
    findings: str,
    ws_send,
    approval_event: asyncio.Event,
) -> str:
    await ws_send(
        ReviewEvent(
            type="human_approval",
            agent="lead",
            message="Review complete. Approve to finalize verdict?",
            severity=None,
        ).to_json()
    )

    await approval_event.wait()

    result = await lead_agent.run(findings)
    return result.output.text
