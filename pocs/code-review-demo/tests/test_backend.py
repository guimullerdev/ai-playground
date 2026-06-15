import pytest
from unittest.mock import patch

from core.backend import get_llm


@patch("core.backend.ChatModel")
def test_default_model_name(MockChatModel, monkeypatch):
    monkeypatch.delenv("OPENAI_CHAT_MODEL", raising=False)
    get_llm()
    call_arg = MockChatModel.from_name.call_args[0][0]
    assert "claude-3.5-haiku" in call_arg


@patch("core.backend.ChatModel")
def test_custom_model_from_env(MockChatModel, monkeypatch):
    monkeypatch.setenv("OPENAI_CHAT_MODEL", "gpt-4o")
    get_llm()
    call_arg = MockChatModel.from_name.call_args[0][0]
    assert "gpt-4o" in call_arg


@patch("core.backend.ChatModel")
def test_returns_chat_model_instance(MockChatModel):
    result = get_llm()
    assert result is MockChatModel.from_name.return_value
