import asyncio
import json
import pytest

from agents.lead_agent import run_lead_with_approval


async def test_emits_human_approval_event(mock_agent, ws_send, approval_event):
    approval_event.set()
    await run_lead_with_approval(mock_agent, "findings", ws_send, approval_event)
    ws_send.assert_called()
    first_call_payload = json.loads(ws_send.call_args_list[0][0][0])
    assert first_call_payload["type"] == "human_approval"


async def test_waits_for_approval_event(mock_agent, ws_send, approval_event):
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(
            run_lead_with_approval(mock_agent, "findings", ws_send, approval_event),
            timeout=0.05,
        )


async def test_resumes_after_approval(mock_agent, ws_send, approval_event):
    approval_event.set()
    await run_lead_with_approval(mock_agent, "findings", ws_send, approval_event)
    mock_agent.run.assert_called_once_with("findings")


async def test_returns_agent_output(mock_agent, ws_send, approval_event):
    approval_event.set()
    result = await run_lead_with_approval(mock_agent, "findings", ws_send, approval_event)
    assert result == mock_agent.run.return_value.output.text


async def test_approval_event_agent_field(mock_agent, ws_send, approval_event):
    approval_event.set()
    await run_lead_with_approval(mock_agent, "findings", ws_send, approval_event)
    first_call_payload = json.loads(ws_send.call_args_list[0][0][0])
    assert first_call_payload["agent"] == "lead"
