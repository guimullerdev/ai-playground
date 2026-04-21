import sys
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

SUMMARIZER_TOOL_SCHEMA = {
    "name": "summarize_text",
    "description": "Summarize a piece of text using a dedicated summarization agent.",
    "input_schema": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The text to summarize",
            }
        },
        "required": ["text"],
    },
}

_SYSTEM_PROMPT = (
    "You are a summarization specialist. "
    "Produce a concise summary in 2-3 sentences that captures the key points. "
    "Be direct and factual. Do not add commentary."
)


def summarize_text(text: str) -> dict:
    """Calls the configured backend (multi-agent orchestration) to summarize the given text."""
    from backend import get_backend
    backend = get_backend()
    messages = [{"role": "user", "content": f"Summarize this:\n\n{text}"}]
    summary = backend.chat(_SYSTEM_PROMPT, messages, [], {})
    return {
        "ok": True,
        "data": {"original_length": len(text), "summary": summary},
        "error": None,
    }
