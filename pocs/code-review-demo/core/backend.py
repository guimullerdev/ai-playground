from beeai_framework.backend import ChatModel


def get_llm() -> ChatModel:
    # OPENAI_API_BASE and OPENAI_API_KEY are read from env
    import os
    model_name = os.getenv("OPENAI_CHAT_MODEL", "anthropic/claude-3.5-haiku")
    return ChatModel.from_name(f"openai:{model_name}")
