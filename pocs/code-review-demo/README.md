# Code Review Demo — BeeAI Multi-Agent Pipeline

A multi-agent code review system built with [BeeAI Framework](https://github.com/i-am-bee/beeai-framework). Five specialized agents collaborate to review a code snippet and produce a final verdict, streamed in real time over WebSocket.

## Architecture

```
POST /review
     │
     ▼
Orchestrator
     ├── handoff ──► Dev Agent        (naming, readability, duplication)
     ├── handoff ──► Security Agent   (injections, eval(), secrets)
     ├── handoff ──► Perf Agent       (complexity, N+1 queries, loops)
     │
     ▼
Lead Agent
     ├── emits "human_approval" ──► client confirms
     └── final verdict: APPROVED | CHANGES_REQUESTED | BLOCKED
```

All agent thoughts, tool calls, and handoffs are pushed to the client as JSON events over `WS /ws`.

## Project Structure

```
code-review-demo/
├── agents/
│   ├── orchestrator.py   # delegates to the 3 specialist agents via HandoffTool
│   ├── dev_agent.py      # code quality reviewer
│   ├── security_agent.py # security auditor (most constrained — thinks before every action)
│   ├── perf_agent.py     # performance reviewer
│   └── lead_agent.py     # consolidates findings + human-in-the-loop approval
├── core/
│   ├── backend.py        # ChatModel factory (OpenRouter via env vars)
│   ├── event_bridge.py   # maps BeeAI emitter events → WebSocket JSON
│   └── models.py         # ReviewEvent dataclass
├── server.py             # FastAPI: POST /review, WS /ws, POST /approve
├── main.py               # entrypoint (loads .env, starts uvicorn)
├── Dockerfile
├── docker-compose.yml
├── start.sh
└── requirements.txt
```

## Quickstart

**1. Configure environment**

```bash
cp .env.example .env
# Edit .env and set your OpenRouter API key
```

**.env.example**
```
OPENAI_API_KEY=your_openrouter_key_here
OPENAI_API_BASE=https://openrouter.ai/api/v1
OPENAI_CHAT_MODEL=anthropic/claude-3.5-haiku
```

**2. Start the server**

```bash
./start.sh
```

The API is available at `http://localhost:8000`. Run in the background with `./start.sh -d`.

## API

### `WS /ws`
Connect first. Receives a stream of `ReviewEvent` JSON messages throughout the pipeline.

### `POST /review`
Start a review. The pipeline runs asynchronously and streams events over the WebSocket.

```json
{ "code": "def authenticate(u, p):\n    ..." }
```

### `POST /approve`
Unblock the Lead Agent after the `human_approval` event is received.

```json
{ "approved": true }
```

## WebSocket Event Types

| `type` | `agent` | Description |
|---|---|---|
| `agent.start` | any | Agent begins its turn |
| `agent.thinking` | any | ThinkTool output |
| `agent.handoff` | orchestrator | Delegating to a specialist |
| `tool.start` | any | Tool invocation begins |
| `tool.end` | any | Tool result returned |
| `finding` | dev / security / perf | An individual code issue |
| `human_approval` | lead | Waiting for `POST /approve` |
| `verdict` | lead | Final verdict text |

Each event has the shape:

```json
{
  "type": "agent.thinking",
  "agent": "security",
  "message": "This f-string builds a raw SQL query...",
  "severity": "critical",
  "timestamp": 1718000000.0
}
```

`severity` is `"critical"`, `"warning"`, `"info"`, or `null`.

## BeeAI Features Used

| Feature | Where |
|---|---|
| `RequirementAgent` (experimental) | All 5 agents |
| `ConditionalRequirement` | Dev Agent (think at step 1), Security Agent (think before and after every tool call) |
| `HandoffTool` | Orchestrator → specialists |
| `UnconstrainedMemory` | Orchestrator, Performance Agent |
| `ThinkTool` | Dev, Security, Perf, Lead agents |
| `GlobalTrajectoryMiddleware` | All agents (feeds the event bridge) |
| `emitter.on("*.*")` | Event Bridge |
| Human-in-the-loop (manual) | Lead Agent via `asyncio.Event` + `POST /approve` |
| OpenAI-compatible backend | OpenRouter via env vars |

## Sample Input

```python
# Intentionally broken — use this to demo the pipeline
def authenticate(username, password):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    result = db.execute(query)
    eval(result["callback"])
    return result
```

Expected output:
- **Dev:** missing type hints, no docstring, no error handling
- **Security:** CRITICAL — SQL injection via f-string; CRITICAL — `eval()` on external data
- **Performance:** no major issues
- **Lead:** requests human approval → **BLOCKED**

## Local Development (without Docker)

```bash
pip install -r requirements.txt
cp .env.example .env  # fill in your key
python main.py
```
