import os
from beeai_framework.backend import ChatModel


def get_llm() -> ChatModel:
    if os.getenv("ANTHROPIC_API_KEY"):
        model = os.getenv("ANTHROPIC_CHAT_MODEL", "claude-sonnet-4-6")
        return ChatModel.from_name(f"anthropic:{model}")

    # fallback: OpenRouter (or any OpenAI-compatible provider)
    model = os.getenv("OPENAI_CHAT_MODEL", "anthropic/claude-3.5-haiku")
    return ChatModel.from_name(f"openai:{model}")
