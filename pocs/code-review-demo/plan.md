# BeeAI Code Review Multi-Agent — Backend Implementation Plan

> **Source of truth:** always check [github.com/i-am-bee/beeai-framework](https://github.com/i-am-bee/beeai-framework) before coding.
> Last synced: 2026-06-10 | Latest Python release: `python_v0.1.81`

---

## Project Structure

```
code-review-demo/
├── agents/
│   ├── orchestrator.py
│   ├── dev_agent.py
│   ├── security_agent.py
│   ├── perf_agent.py
│   └── lead_agent.py
├── core/
│   ├── backend.py          # OpenRouter config
│   ├── event_bridge.py     # BeeAI events → WebSocket
│   └── models.py           # JSON event types
├── server.py               # FastAPI + WebSocket
├── main.py                 # entrypoint
├── .env                    # gitignored
└── .env.example
```

---

## 1. LLM Backend — OpenRouter

BeeAI uses the OpenAI provider internally. OpenRouter is OpenAI-compatible, so it just needs
the right env vars — no custom adapter needed.

```bash
# .env.example
OPENAI_API_KEY=your_openrouter_key_here
OPENAI_API_BASE=https://openrouter.ai/api/v1
OPENAI_CHAT_MODEL=anthropic/claude-3.5-haiku
```

```python
# core/backend.py
# No custom code needed — BeeAI reads env vars automatically.
# Just call:
from beeai_framework.backend import ChatModel

def get_llm():
    return ChatModel.from_name("openai:anthropic/claude-3.5-haiku")
    # OPENAI_API_BASE and OPENAI_API_KEY are picked up from env
```

> ⚠️ If using models that don't support `response_format.strict` (e.g. some OpenRouter models),
> set `OPENAI_API_HEADERS` or downgrade structured output. This is a known issue (#980 on GitHub).

### Recommended models on OpenRouter

| Model | Notes |
|---|---|
| `anthropic/claude-3.5-haiku` | Fast, strong reasoning — best for demo |
| `google/gemini-flash-1.5` | Very cheap for testing |
| `meta-llama/llama-3.1-8b-instruct` | Free tier available |

---

## 2. Correct Import Paths (as of v0.1.81)

> ⚠️ `RequirementAgent` is still under `experimental`. Use these exact imports:

```python
from beeai_framework.agents.experimental import RequirementAgent
from beeai_framework.agents.experimental.requirements.conditional import ConditionalRequirement
from beeai_framework.backend import ChatModel
from beeai_framework.errors import FrameworkError
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.tools import Tool
from beeai_framework.tools.handoff import HandoffTool
from beeai_framework.tools.think import ThinkTool
```

---

## 3. The 5 Agents

### Orchestrator
- Receives the code, plans the review, delegates to the 3 specialist agents in sequence
- **BeeAI features:** `HandoffTool` (one per specialist), `UnconstrainedMemory`

### Dev Agent
- Reviews: naming conventions, code patterns, readability, duplication
- **BeeAI features:** `RequirementAgent` with specific `role` + `instructions`,
  `ConditionalRequirement(ThinkTool, force_at_step=1)`

### Security Agent
- Reviews: injection vulnerabilities, exposed secrets, `eval()` usage, unsanitized inputs
- **BeeAI features:**
  - `ConditionalRequirement(ThinkTool, force_at_step=1)` — always thinks before acting
  - `ConditionalRequirement(ThinkTool, force_after=Tool, consecutive_allowed=False)` — thinks after every tool call
- Most cautious agent by design

### Performance Agent
- Reviews: algorithmic complexity, nested loops, N+1 queries
- **BeeAI features:** `RequirementAgent` with `UnconstrainedMemory` to cross-reference prior findings

### Lead Agent
- Consolidates all findings, emits the final verdict
- **BeeAI features:** Human-in-the-loop via event emission (UI surfaces a confirmation button)
- Receives all prior findings as context in its prompt
- Emits a `human_approval` WebSocket event before finalizing verdict

> ⚠️ `AskPermissionRequirement` was listed in docs but **not yet confirmed stable in Python**.
> Implement human-in-the-loop manually via a WebSocket event + `asyncio.Event` for now.

---

## 4. Event Bridge — Real-Time Stream

Every BeeAI internal event is mapped to a standardized JSON message and pushed via WebSocket.

### Event model

```python
# core/models.py
from dataclasses import dataclass, asdict
from typing import Literal
import time, json

@dataclass
class ReviewEvent:
    type: Literal[
        "agent.start",
        "agent.thinking",
        "agent.handoff",
        "tool.start",
        "tool.end",
        "finding",
        "human_approval",
        "verdict"
    ]
    agent: str            # "orchestrator" | "dev" | "security" | "perf" | "lead"
    message: str          # text for the thought stream
    severity: str | None  # "critical" | "warning" | "info" | None
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

    def to_json(self) -> str:
        return json.dumps(asdict(self))
```

### Bridge implementation

```python
# core/event_bridge.py
from core.models import ReviewEvent

async def attach_bridge(agent, ws_send, agent_name: str):
    @agent.emitter.on("*.*")
    async def handle(data, event):
        review_event = _map_event(event.name, data, agent_name)
        if review_event:
            await ws_send(review_event.to_json())

def _map_event(event_name: str, data, agent_name: str) -> ReviewEvent | None:
    if "think" in event_name:
        return ReviewEvent(type="agent.thinking", agent=agent_name, message=str(data), severity=None)
    if "tool" in event_name and "start" in event_name:
        return ReviewEvent(type="tool.start", agent=agent_name, message=f"Using tool: {event_name}", severity=None)
    if "tool" in event_name and "end" in event_name:
        return ReviewEvent(type="tool.end", agent=agent_name, message=str(data), severity=None)
    return None
```

> Refine `_map_event` as you discover real event names via `GlobalTrajectoryMiddleware` logs.

---

## 5. WebSocket Server

```
POST /review   — body: { "code": "<source code>" }
WS   /ws       — stream of ReviewEvent JSON messages
POST /approve  — body: { "approved": true|false }  ← human-in-the-loop response
```

### Request lifecycle

```
1. Client connects to WS /ws
2. Client sends POST /review with the code snippet
3. Server starts the agent pipeline in background (asyncio task)
4. Each BeeAI event is forwarded through the WebSocket in real time
5. Lead Agent emits "human_approval" event → UI shows confirmation button
6. Client sends POST /approve → pipeline resumes
7. Final "verdict" event is sent and the stream ends
```

---

## 6. Agent Pipeline & Execution Flow

```
POST /review
     │
     ▼
Orchestrator.run(code)
     │
     ├── handoff ──► Dev Agent ───────► findings_dev[]
     │
     ├── handoff ──► Security Agent ──► findings_sec[]
     │
     ├── handoff ──► Perf Agent ──────► findings_perf[]
     │
     ▼
Lead Agent.run(all_findings)
     │
     ├── emit "human_approval" ──► UI shows button
     │   asyncio.Event().wait()  ◄── POST /approve unblocks this
     │
     ▼
verdict: APPROVED | CHANGES_REQUESTED | BLOCKED
```

Agents run **sequentially** by default — keeps the thought stream readable.
Can switch to `asyncio.gather()` for parallel execution if speed matters more.

---

## 7. BeeAI Features Coverage

| Feature | Where it's used |
|---|---|
| `RequirementAgent` (experimental) | All 5 agents |
| `ConditionalRequirement` | Dev, Security agents |
| Human-in-the-loop (manual) | Lead Agent via `asyncio.Event` |
| `HandoffTool` | Orchestrator → specialists |
| `UnconstrainedMemory` | Orchestrator, Performance Agent |
| `ThinkTool` | Dev Agent, Security Agent |
| `GlobalTrajectoryMiddleware` | All agents (feeds the event bridge) |
| `emitter.on("*.*")` | Event Bridge (real-time WS stream) |
| OpenAI-compatible backend | OpenRouter via env vars |

---

## 8. Dependencies

```txt
# requirements.txt
beeai-framework
fastapi
uvicorn[standard]
python-dotenv
```

> No `websockets` package needed — FastAPI handles WebSocket natively.

---

## 9. Implementation Order

| Step | File | Goal |
|---|---|---|
| 1 | `.env` + `core/backend.py` | Connect to OpenRouter, validate a single LLM call |
| 2 | `agents/security_agent.py` | Most complex agent — validate constraints work |
| 3 | `core/event_bridge.py` | Capture BeeAI events, log to console first |
| 4 | Remaining agents | Dev, Perf, Lead, Orchestrator |
| 5 | `server.py` | FastAPI WebSocket + REST endpoints |
| 6 | `main.py` | Wire everything, end-to-end test |

---

## 10. Sample Input for the Demo

```python
# Intentionally broken code — SQL injection + eval + no error handling
def authenticate(username, password):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    result = db.execute(query)
    eval(result["callback"])
    return result
```

Expected pipeline output:
- **Dev:** missing type hints, no docstring, no error handling
- **Security:** 🔴 CRITICAL — SQL injection via f-string, 🔴 CRITICAL — `eval()` on external data
- **Performance:** no major issues
- **Lead:** requests human approval → **BLOCKED**