import sys
import os
import json

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend import get_backend
from agents.assistant import ASSISTANT_NAME, ASSISTANT_DESCRIPTION, ASSISTANT_SYSTEM_PROMPT
from agents.creative import CREATIVE_NAME, CREATIVE_DESCRIPTION, CREATIVE_SYSTEM_PROMPT
from agents.critic import CRITIC_NAME, CRITIC_DESCRIPTION, CRITIC_SYSTEM_PROMPT
from tools.weather import get_weather, WEATHER_TOOL_SCHEMA
from tools.search import search_web, SEARCH_TOOL_SCHEMA
from tools.calculator import calculate, CALCULATOR_TOOL_SCHEMA
from tools.summarizer import summarize_text, SUMMARIZER_TOOL_SCHEMA

app = FastAPI()

AGENTS = {
    ASSISTANT_NAME: {"name": ASSISTANT_NAME, "description": ASSISTANT_DESCRIPTION, "system": ASSISTANT_SYSTEM_PROMPT},
    CREATIVE_NAME:  {"name": CREATIVE_NAME,  "description": CREATIVE_DESCRIPTION,  "system": CREATIVE_SYSTEM_PROMPT},
    CRITIC_NAME:    {"name": CRITIC_NAME,    "description": CRITIC_DESCRIPTION,    "system": CRITIC_SYSTEM_PROMPT},
}

TOOLS = [WEATHER_TOOL_SCHEMA, SEARCH_TOOL_SCHEMA, CALCULATOR_TOOL_SCHEMA, SUMMARIZER_TOOL_SCHEMA]

TOOL_FNS = {
    "get_weather": get_weather,
    "search_web": search_web,
    "calculate": calculate,
    "summarize_text": summarize_text,
}

# In-memory histories per agent (OpenAI message format)
histories: dict = {name: [] for name in AGENTS}


class ChatRequest(BaseModel):
    message: str


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


async def run_chat_stream(agent_name: str, user_message: str):
    agent = AGENTS[agent_name]
    messages = histories[agent_name]
    messages.append({"role": "user", "content": user_message})

    backend = get_backend()
    async for event in backend.stream(agent["system"], messages, TOOLS, TOOL_FNS):
        yield _sse(event)


@app.get("/agents")
def get_agents():
    return [{"name": a["name"], "description": a["description"]} for a in AGENTS.values()]


@app.post("/chat/{agent_name}")
async def chat(agent_name: str, body: ChatRequest):
    if agent_name not in AGENTS:
        raise HTTPException(status_code=404, detail="Agent not found")
    return StreamingResponse(
        run_chat_stream(agent_name, body.message),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/history/{agent_name}")
def get_history(agent_name: str):
    if agent_name not in AGENTS:
        raise HTTPException(status_code=404, detail="Agent not found")
    readable = []
    for msg in histories[agent_name]:
        role = msg.get("role")
        content = msg.get("content")
        if role in ("user", "assistant") and isinstance(content, str) and content:
            readable.append({"role": role, "content": content})
    return readable


@app.delete("/history/{agent_name}")
def clear_history(agent_name: str):
    if agent_name not in AGENTS:
        raise HTTPException(status_code=404, detail="Agent not found")
    histories[agent_name] = []
    return {"ok": True}


# Serve frontend — must be last to avoid catching API routes
app.mount("/", StaticFiles(directory=os.path.join(_ROOT, "app", "static"), html=True), name="static")
