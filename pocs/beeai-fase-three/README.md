# BeeAI Phase Three

Multi-personality agents with tool use and security testing, built with the Anthropic API and Rich TUI.

## Agents

| Agent | Personality |
|---|---|
| Assistant | Helpful, concise, professional |
| Creative | Imaginative, lateral thinking |
| Critic | Skeptical, challenges assumptions |

## Setup

Copy the example env file and add your Anthropic API key:

```bash
cp .env.example .env
```

## Running with Docker (recommended)

**Web UI** — open http://localhost:8000 after starting:
```bash
docker compose up web
```

**Terminal chat app:**
```bash
docker compose run --rm chat
```

**Security tests:**
```bash
docker compose run --rm security-tests
```

## Running locally

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...

uvicorn app.server:app --reload   # web UI at http://localhost:8000
python3 app/main.py               # terminal chat app
python3 security/tests.py         # security tests
```

## Terminal chat commands

| Command | Action |
|---|---|
| `/switch` | Switch to a different agent |
| `/history` | View conversation log |
| `/help` | Show commands |
| `/quit` | Exit |
