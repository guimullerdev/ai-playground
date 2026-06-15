import json
import pytest
from core.models import ReviewEvent


def test_to_json_roundtrip():
    evt = ReviewEvent(type="finding", agent="dev", message="issue found", severity="warning")
    data = json.loads(evt.to_json())
    assert data["type"] == "finding"
    assert data["agent"] == "dev"
    assert data["message"] == "issue found"
    assert data["severity"] == "warning"
    assert "timestamp" in data


def test_timestamp_auto_set():
    evt = ReviewEvent(type="agent.start", agent="orchestrator", message="hi", severity=None)
    assert evt.timestamp is not None
    assert isinstance(evt.timestamp, float)


def test_timestamp_explicit():
    evt = ReviewEvent(type="agent.start", agent="orchestrator", message="hi", severity=None, timestamp=1234567890.0)
    assert evt.timestamp == 1234567890.0


def test_all_event_types():
    types = [
        "agent.start",
        "agent.thinking",
        "agent.handoff",
        "tool.start",
        "tool.end",
        "finding",
        "human_approval",
        "verdict",
    ]
    for t in types:
        evt = ReviewEvent(type=t, agent="x", message="m", severity=None)
        assert evt.type == t


def test_severity_none():
    evt = ReviewEvent(type="agent.start", agent="x", message="m", severity=None)
    data = json.loads(evt.to_json())
    assert data["severity"] is None
