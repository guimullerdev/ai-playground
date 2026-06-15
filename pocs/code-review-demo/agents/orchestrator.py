from beeai_framework.agents.experimental import RequirementAgent
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.tools.handoff import HandoffTool
from core.backend import get_llm


def create_orchestrator(dev_agent, security_agent, perf_agent) -> RequirementAgent:
    return RequirementAgent(
        llm=get_llm(),
        memory=UnconstrainedMemory(),
        tools=[
            HandoffTool(target=dev_agent, name="handoff_dev"),
            HandoffTool(target=security_agent, name="handoff_security"),
            HandoffTool(target=perf_agent, name="handoff_perf"),
        ],
        role="orchestrator",
        instructions=(
            "You are a senior engineering manager orchestrating a code review. "
            "Given a code snippet, delegate it to the dev, security, and performance agents "
            "in that order using the handoff tools. Collect their findings and return all of them."
        ),
    )
