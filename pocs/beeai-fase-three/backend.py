from __future__ import annotations

"""
Unified backend abstraction.

Backends:
  - openrouter  (default): OpenAI-compatible API via OpenRouter. Free models available.
  - claude-code: Uses claude-code-sdk with your existing Claude Code auth. No API key needed.

Select backend with env var BACKEND=openrouter|claude-code.
"""

import os
import json
import asyncio
from typing import AsyncGenerator

BACKEND_TYPE = os.getenv("BACKEND", "openrouter")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_HEADERS = {"HTTP-Referer": "https://github.com/beeai-demo", "X-Title": "BeeAI Phase Three"}


# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------

def _to_openai_tools(tools: list[dict]) -> list[dict]:
    """Convert Anthropic tool schema format to OpenAI tool schema format."""
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["input_schema"],
            },
        }
        for t in tools
    ]


# ---------------------------------------------------------------------------
# OpenRouter backend
# ---------------------------------------------------------------------------

class OpenRouterBackend:
    """Calls OpenRouter (OpenAI-compatible) with full tool-calling support."""

    def __init__(self):
        from openai import AsyncOpenAI, OpenAI
        self.async_client = AsyncOpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            default_headers=OPENROUTER_HEADERS,
        )
        self.sync_client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            default_headers=OPENROUTER_HEADERS,
        )
        self.model = OPENROUTER_MODEL

    async def stream(
        self,
        system: str,
        messages: list,
        tools: list,
        tool_fns: dict,
    ) -> AsyncGenerator[dict, None]:
        """
        Full agentic loop with streaming.

        messages: mutable list of OpenAI-format message dicts (history); appended in-place.
        Yields event dicts:
          {"type": "text_delta", "content": str}
          {"type": "tool_call", "name": str, "input": dict}
          {"type": "tool_result", "name": str, "ok": bool, "error": str|None}
          {"type": "done"}
        """
        openai_tools = _to_openai_tools(tools) if tools else []

        while True:
            full_text = ""
            tool_calls_acc: dict[int, dict] = {}

            kwargs: dict = {
                "model": self.model,
                "messages": [{"role": "system", "content": system}] + messages,
                "stream": True,
            }
            if openai_tools:
                kwargs["tools"] = openai_tools
                kwargs["tool_choice"] = "auto"

            stream = await self.async_client.chat.completions.create(**kwargs)
            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta

                if delta.content:
                    full_text += delta.content
                    yield {"type": "text_delta", "content": delta.content}

                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_acc:
                            tool_calls_acc[idx] = {"id": "", "name": "", "arguments": ""}
                        if tc.id:
                            tool_calls_acc[idx]["id"] = tc.id
                        if tc.function and tc.function.name:
                            tool_calls_acc[idx]["name"] += tc.function.name
                        if tc.function and tc.function.arguments:
                            tool_calls_acc[idx]["arguments"] += tc.function.arguments

            if not tool_calls_acc:
                if full_text:
                    messages.append({"role": "assistant", "content": full_text})
                yield {"type": "done"}
                break

            # Append assistant turn with tool calls
            messages.append({
                "role": "assistant",
                "content": full_text or None,
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {"name": tc["name"], "arguments": tc["arguments"]},
                    }
                    for tc in tool_calls_acc.values()
                ],
            })

            # Execute each tool
            for tc in tool_calls_acc.values():
                try:
                    args = json.loads(tc["arguments"])
                except (json.JSONDecodeError, ValueError):
                    args = {}
                yield {"type": "tool_call", "name": tc["name"], "input": args}
                fn = tool_fns.get(tc["name"])
                if fn:
                    result = await asyncio.to_thread(fn, **args)
                else:
                    result = {"ok": False, "data": None, "error": f"Unknown tool: {tc['name']}"}
                yield {
                    "type": "tool_result",
                    "name": tc["name"],
                    "ok": result["ok"],
                    "error": result.get("error"),
                }
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": json.dumps(result),
                })

    def chat(self, system: str, messages: list, tools: list, tool_fns: dict) -> str:
        """Synchronous agentic loop. Appends to messages in-place. Returns final text."""
        openai_tools = _to_openai_tools(tools) if tools else []

        while True:
            kwargs: dict = {
                "model": self.model,
                "messages": [{"role": "system", "content": system}] + messages,
            }
            if openai_tools:
                kwargs["tools"] = openai_tools
                kwargs["tool_choice"] = "auto"

            response = self.sync_client.chat.completions.create(**kwargs)
            msg = response.choices[0].message

            if not msg.tool_calls:
                text = msg.content or ""
                messages.append({"role": "assistant", "content": text})
                return text

            # Append assistant turn with tool calls
            messages.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in msg.tool_calls
                ],
            })

            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except (json.JSONDecodeError, ValueError):
                    args = {}
                fn = tool_fns.get(tc.function.name)
                if fn:
                    result = fn(**args)
                else:
                    result = {"ok": False, "data": None, "error": f"Unknown tool: {tc.function.name}"}
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result),
                })


# ---------------------------------------------------------------------------
# Claude Code SDK backend
# ---------------------------------------------------------------------------

class ClaudeCodeBackend:
    """
    Uses claude-code-sdk — no API key required, leverages your existing Claude Code session.
    Custom Python tools are not supported in this mode (tool calls are skipped).
    Requires Python 3.10+ and the 'claude' CLI to be installed.
    """

    async def stream(
        self,
        system: str,
        messages: list,
        tools: list,
        tool_fns: dict,
    ) -> AsyncGenerator[dict, None]:
        from claude_code_sdk import query, ClaudeCodeOptions

        # Extract the last user message from history
        user_msg = next(
            (
                m["content"]
                for m in reversed(messages)
                if m.get("role") == "user" and isinstance(m.get("content"), str)
            ),
            "",
        )

        options = ClaudeCodeOptions(system_prompt=system)
        full_text = ""

        async for event in query(prompt=user_msg, options=options):
            # Handle AssistantMessage blocks
            content = getattr(event, "content", None)
            if content and isinstance(content, list):
                for block in content:
                    text = getattr(block, "text", None)
                    if text:
                        full_text += text
                        yield {"type": "text_delta", "content": text}

        messages.append({"role": "assistant", "content": full_text})
        yield {"type": "done"}

    def chat(self, system: str, messages: list, tools: list, tool_fns: dict) -> str:
        """Run the async stream in a fresh event loop (safe from sync context)."""
        result: list[dict] = []
        exc: list[Exception] = []

        async def _collect():
            async for event in self.stream(system, messages, tools, tool_fns):
                result.append(event)

        import threading

        def _run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(_collect())
            except Exception as e:
                exc.append(e)
            finally:
                loop.close()

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join()

        if exc:
            raise exc[0]

        return "".join(e["content"] for e in result if e["type"] == "text_delta")


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_instance: OpenRouterBackend | ClaudeCodeBackend | None = None


def get_backend() -> OpenRouterBackend | ClaudeCodeBackend:
    global _instance
    if _instance is None:
        if BACKEND_TYPE == "claude-code":
            _instance = ClaudeCodeBackend()
        else:
            _instance = OpenRouterBackend()
    return _instance
