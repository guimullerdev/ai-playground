import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock


@pytest.fixture
def mock_llm():
    return MagicMock()


@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.emitter.on.return_value = lambda f: f

    run_result = MagicMock()
    run_result.output.text = "APPROVED"
    agent.run = AsyncMock(return_value=run_result)
    return agent


@pytest.fixture
def ws_send():
    return AsyncMock()


@pytest.fixture
def approval_event():
    event = asyncio.Event()
    event.clear()
    return event
