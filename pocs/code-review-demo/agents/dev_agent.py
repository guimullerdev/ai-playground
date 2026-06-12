from beeai_framework.agents.experimental import RequirementAgent
from beeai_framework.agents.experimental.requirements.conditional import ConditionalRequirement
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.tools.think import ThinkTool
from core.backend import get_llm


def create_dev_agent() -> RequirementAgent:
    return RequirementAgent(
        llm=get_llm(),
        memory=UnconstrainedMemory(),
        tools=[ThinkTool()],
        requirements=[
            ConditionalRequirement(ThinkTool, force_at_step=1),
        ],
        role="dev_reviewer",
        instructions=(
            "You are a senior software engineer reviewing code quality. "
            "Focus on: naming conventions, code patterns, readability, and duplication. "
            "Think carefully before responding. Report each issue with a severity: info, warning, or critical."
        ),
    )
