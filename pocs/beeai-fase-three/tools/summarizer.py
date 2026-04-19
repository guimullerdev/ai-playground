from anthropic import Anthropic

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
    """Calls a second agent (multi-agent orchestration) to summarize the given text."""
    client = Anthropic()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Summarize this:\n\n{text}"}],
    )
    summary = response.content[0].text
    return {
        "ok": True,
        "data": {"original_length": len(text), "summary": summary},
        "error": None,
    }
