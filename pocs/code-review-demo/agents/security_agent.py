from beeai_framework.agents.experimental import RequirementAgent
from beeai_framework.agents.experimental.requirements.conditional import ConditionalRequirement
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.tools import Tool
from beeai_framework.tools.think import ThinkTool
from core.backend import get_llm


def create_security_agent() -> RequirementAgent:
    return RequirementAgent(
        llm=get_llm(),
        memory=UnconstrainedMemory(),
        tools=[ThinkTool()],
        requirements=[
            ConditionalRequirement(ThinkTool, force_at_step=1),
            ConditionalRequirement(ThinkTool, force_after=Tool, consecutive_allowed=False),
        ],
        role="security_reviewer",
        instructions=(
            "You are a security engineer performing a thorough code security audit. "
            "Focus on: SQL injection, command injection, exposed secrets, eval() on external data, "
            "and unsanitized inputs. Always think before and after each finding. "
            "Mark every issue as critical, warning, or info."
        ),
    )
