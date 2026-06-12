from beeai_framework.agents.experimental import RequirementAgent
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.tools.think import ThinkTool
from core.backend import get_llm


def create_perf_agent() -> RequirementAgent:
    return RequirementAgent(
        llm=get_llm(),
        memory=UnconstrainedMemory(),
        tools=[ThinkTool()],
        role="performance_reviewer",
        instructions=(
            "You are a performance engineer reviewing code efficiency. "
            "Focus on: algorithmic complexity, nested loops, N+1 queries, and unnecessary allocations. "
            "Cross-reference any findings against prior notes in memory. "
            "Report each issue with a severity: info, warning, or critical."
        ),
    )
