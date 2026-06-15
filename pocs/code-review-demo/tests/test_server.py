import asyncio
import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

import httpx
from httpx import ASGITransport
from starlette.testclient import TestClient

import server
from server import app


@pytest.fixture(autouse=True)
def reset_server_state():
    server._approval_event.clear()
    server._active_ws = None
    yield
    server._approval_event.clear()
    server._active_ws = None


# ── HTTP endpoints ────────────────────────────────────────────────────────────

async def test_get_root_returns_html():
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@patch("server._run_pipeline", new_callable=AsyncMock)
async def test_post_review_starts_pipeline(mock_pipeline):
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/review", json={"code": "x = 1"})
    assert response.json() == {"status": "started"}


@patch("server._run_pipeline", new_callable=AsyncMock)
async def test_post_review_spawns_task(mock_pipeline):
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/review", json={"code": "def foo(): pass"})
    mock_pipeline.assert_called_once_with("def foo(): pass")


async def test_post_approve_sets_event():
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/approve", json={"approved": True})
    assert server._approval_event.is_set()


async def test_post_approve_false_does_not_set():
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/approve", json={"approved": False})
    assert not server._approval_event.is_set()


async def test_post_approve_returns_ok():
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/approve", json={"approved": True})
    assert response.json() == {"status": "ok"}


# ── WebSocket endpoint ────────────────────────────────────────────────────────

def test_ws_accepts_connection():
    with TestClient(app) as client:
        with client.websocket_connect("/ws"):
            pass


async def test_ws_receives_sent_message():
    mock_ws = AsyncMock()
    server._active_ws = mock_ws
    await server._ws_send("hello")
    mock_ws.send_text.assert_called_once_with("hello")


def test_ws_disconnect_clears_active_ws():
    with TestClient(app) as client:
        with client.websocket_connect("/ws"):
            assert server._active_ws is not None
    assert server._active_ws is None
