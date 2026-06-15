import pytest
from unittest.mock import patch, MagicMock, call

from agents.dev_agent import create_dev_agent
from agents.security_agent import create_security_agent
from agents.perf_agent import create_perf_agent
from agents.orchestrator import create_orchestrator


# ── Dev agent ────────────────────────────────────────────────────────────────

@patch("agents.dev_agent.UnconstrainedMemory")
@patch("agents.dev_agent.ConditionalRequirement")
@patch("agents.dev_agent.ThinkTool")
@patch("agents.dev_agent.RequirementAgent")
@patch("agents.dev_agent.get_llm")
def test_dev_agent_has_think_tool(mock_get_llm, MockAgent, MockThinkTool, MockCondReq, MockMemory, mock_llm):
    mock_get_llm.return_value = mock_llm
    create_dev_agent()
    kwargs = MockAgent.call_args.kwargs
    assert MockThinkTool.return_value in kwargs["tools"]


@patch("agents.dev_agent.UnconstrainedMemory")
@patch("agents.dev_agent.ConditionalRequirement")
@patch("agents.dev_agent.ThinkTool")
@patch("agents.dev_agent.RequirementAgent")
@patch("agents.dev_agent.get_llm")
def test_dev_agent_has_conditional_requirement(mock_get_llm, MockAgent, MockThinkTool, MockCondReq, MockMemory, mock_llm):
    mock_get_llm.return_value = mock_llm
    create_dev_agent()
    MockCondReq.assert_called_once_with(MockThinkTool, force_at_step=1)
    kwargs = MockAgent.call_args.kwargs
    assert MockCondReq.return_value in kwargs["requirements"]


@patch("agents.dev_agent.UnconstrainedMemory")
@patch("agents.dev_agent.ConditionalRequirement")
@patch("agents.dev_agent.ThinkTool")
@patch("agents.dev_agent.RequirementAgent")
@patch("agents.dev_agent.get_llm")
def test_dev_agent_role(mock_get_llm, MockAgent, MockThinkTool, MockCondReq, MockMemory, mock_llm):
    mock_get_llm.return_value = mock_llm
    create_dev_agent()
    kwargs = MockAgent.call_args.kwargs
    assert kwargs["role"] == "dev_reviewer"


# ── Security agent ────────────────────────────────────────────────────────────

@patch("agents.security_agent.UnconstrainedMemory")
@patch("agents.security_agent.ConditionalRequirement")
@patch("agents.security_agent.ThinkTool")
@patch("agents.security_agent.RequirementAgent")
@patch("agents.security_agent.get_llm")
def test_security_agent_has_two_requirements(mock_get_llm, MockAgent, MockThinkTool, MockCondReq, MockMemory, mock_llm):
    mock_get_llm.return_value = mock_llm
    create_security_agent()
    kwargs = MockAgent.call_args.kwargs
    assert len(kwargs["requirements"]) == 2


@patch("agents.security_agent.UnconstrainedMemory")
@patch("agents.security_agent.ConditionalRequirement")
@patch("agents.security_agent.ThinkTool")
@patch("agents.security_agent.RequirementAgent")
@patch("agents.security_agent.get_llm")
def test_security_agent_force_at_step_1(mock_get_llm, MockAgent, MockThinkTool, MockCondReq, MockMemory, mock_llm):
    mock_get_llm.return_value = mock_llm
    create_security_agent()
    first_call = MockCondReq.call_args_list[0]
    assert first_call == call(MockThinkTool, force_at_step=1)


@patch("agents.security_agent.Tool")
@patch("agents.security_agent.UnconstrainedMemory")
@patch("agents.security_agent.ConditionalRequirement")
@patch("agents.security_agent.ThinkTool")
@patch("agents.security_agent.RequirementAgent")
@patch("agents.security_agent.get_llm")
def test_security_agent_force_after_tool(mock_get_llm, MockAgent, MockThinkTool, MockCondReq, MockMemory, MockTool, mock_llm):
    mock_get_llm.return_value = mock_llm
    create_security_agent()
    second_call = MockCondReq.call_args_list[1]
    assert second_call == call(MockThinkTool, force_after=MockTool, consecutive_allowed=False)


@patch("agents.security_agent.UnconstrainedMemory")
@patch("agents.security_agent.ConditionalRequirement")
@patch("agents.security_agent.ThinkTool")
@patch("agents.security_agent.RequirementAgent")
@patch("agents.security_agent.get_llm")
def test_security_agent_role(mock_get_llm, MockAgent, MockThinkTool, MockCondReq, MockMemory, mock_llm):
    mock_get_llm.return_value = mock_llm
    create_security_agent()
    kwargs = MockAgent.call_args.kwargs
    assert kwargs["role"] == "security_reviewer"


# ── Perf agent ────────────────────────────────────────────────────────────────

@patch("agents.perf_agent.UnconstrainedMemory")
@patch("agents.perf_agent.ThinkTool")
@patch("agents.perf_agent.RequirementAgent")
@patch("agents.perf_agent.get_llm")
def test_perf_agent_has_think_tool(mock_get_llm, MockAgent, MockThinkTool, MockMemory, mock_llm):
    mock_get_llm.return_value = mock_llm
    create_perf_agent()
    kwargs = MockAgent.call_args.kwargs
    assert MockThinkTool.return_value in kwargs["tools"]


@patch("agents.perf_agent.UnconstrainedMemory")
@patch("agents.perf_agent.ThinkTool")
@patch("agents.perf_agent.RequirementAgent")
@patch("agents.perf_agent.get_llm")
def test_perf_agent_has_memory(mock_get_llm, MockAgent, MockThinkTool, MockMemory, mock_llm):
    mock_get_llm.return_value = mock_llm
    create_perf_agent()
    kwargs = MockAgent.call_args.kwargs
    assert kwargs["memory"] is MockMemory.return_value


@patch("agents.perf_agent.UnconstrainedMemory")
@patch("agents.perf_agent.ThinkTool")
@patch("agents.perf_agent.RequirementAgent")
@patch("agents.perf_agent.get_llm")
def test_perf_agent_role(mock_get_llm, MockAgent, MockThinkTool, MockMemory, mock_llm):
    mock_get_llm.return_value = mock_llm
    create_perf_agent()
    kwargs = MockAgent.call_args.kwargs
    assert kwargs["role"] == "performance_reviewer"


# ── Orchestrator ──────────────────────────────────────────────────────────────

@patch("agents.orchestrator.HandoffTool")
@patch("agents.orchestrator.UnconstrainedMemory")
@patch("agents.orchestrator.RequirementAgent")
@patch("agents.orchestrator.get_llm")
def test_orchestrator_has_three_handoff_tools(mock_get_llm, MockAgent, MockMemory, MockHandoff, mock_llm):
    mock_get_llm.return_value = mock_llm
    create_orchestrator(MagicMock(), MagicMock(), MagicMock())
    kwargs = MockAgent.call_args.kwargs
    assert len(kwargs["tools"]) == 3


@patch("agents.orchestrator.HandoffTool")
@patch("agents.orchestrator.UnconstrainedMemory")
@patch("agents.orchestrator.RequirementAgent")
@patch("agents.orchestrator.get_llm")
def test_orchestrator_handoff_names(mock_get_llm, MockAgent, MockMemory, MockHandoff, mock_llm):
    mock_get_llm.return_value = mock_llm
    create_orchestrator(MagicMock(), MagicMock(), MagicMock())
    names = {c.kwargs["name"] for c in MockHandoff.call_args_list}
    assert names == {"handoff_dev", "handoff_security", "handoff_perf"}


@patch("agents.orchestrator.HandoffTool")
@patch("agents.orchestrator.UnconstrainedMemory")
@patch("agents.orchestrator.RequirementAgent")
@patch("agents.orchestrator.get_llm")
def test_orchestrator_role(mock_get_llm, MockAgent, MockMemory, MockHandoff, mock_llm):
    mock_get_llm.return_value = mock_llm
    create_orchestrator(MagicMock(), MagicMock(), MagicMock())
    kwargs = MockAgent.call_args.kwargs
    assert kwargs["role"] == "orchestrator"
