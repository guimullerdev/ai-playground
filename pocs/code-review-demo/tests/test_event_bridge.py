import json
import pytest
from unittest.mock import MagicMock, AsyncMock
from core.event_bridge import _map_event, attach_bridge


class _FakeEvent:
    def __init__(self, name):
        self.name = name


def test_think_event():
    evt = _map_event("agent.think.start", "some thought", "dev")
    assert evt is not None
    assert evt.type == "agent.thinking"


def test_tool_start_event():
    evt = _map_event("tool.call.start", {}, "dev")
    assert evt is not None
    assert evt.type == "tool.start"


def test_tool_end_event():
    evt = _map_event("tool.call.end", {}, "dev")
    assert evt is not None
    assert evt.type == "tool.end"


def test_unknown_event_returns_none():
    evt = _map_event("agent.start", {}, "dev")
    assert evt is None


def test_message_includes_agent_name():
    evt = _map_event("agent.think.start", "thought", "security")
    assert evt.agent == "security"


async def test_attach_bridge_registers_handler():
    agent = MagicMock()
    agent.emitter.on.return_value = lambda f: f
    ws_send = AsyncMock()

    await attach_bridge(agent, ws_send, "orchestrator")

    agent.emitter.on.assert_called_once_with("*.*")


async def test_attach_bridge_calls_ws_send(ws_send):
    agent = MagicMock()
    captured = {}

    def capture_on(pattern):
        def decorator(fn):
            captured["handler"] = fn
            return fn
        return decorator

    agent.emitter.on.side_effect = capture_on

    await attach_bridge(agent, ws_send, "dev")

    await captured["handler"]("a thought", _FakeEvent("agent.think.start"))

    ws_send.assert_called_once()
    data = json.loads(ws_send.call_args[0][0])
    assert data["type"] == "agent.thinking"
    assert data["agent"] == "dev"
