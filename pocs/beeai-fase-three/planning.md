# BeeAI Phase Three - Project Planning

## Goal
Build a simple interactive demo that showcases the core capabilities of BeeAI: agent personalities, tool/function usage, and basic security boundaries.

---

## Core Ideas

### 1. Multi-Personality Agents
Create multiple agents with distinct personalities that the user can interact with:
- **Assistant Agent** — helpful, concise, professional
- **Creative Agent** — imaginative, exploratory, lateral thinking
- **Critic Agent** — skeptical, challenges assumptions, asks hard questions

Each agent shares the same underlying model but has a different system prompt and behavioral profile. The demo should make the personality differences obvious through conversation.

### 2. Tool / Function Use
Give agents access to a small set of tools to demonstrate function-calling:
- `get_weather(city)` — mock or real weather API call
- `search_web(query)` — web search (mock or real)
- `calculate(expression)` — safe math evaluator
- `summarize_text(text)` — call another BeeAI agent to summarize

The demo should show the full tool-call loop: user asks something, agent decides to call a tool, tool returns result, agent incorporates it in the reply.

### 3. Interactive App
A terminal-based or simple web UI that lets the user:
- Choose which agent personality to talk to
- See the agent's reasoning/tool calls in real time (streaming)
- Switch agents mid-conversation and see how the same question gets different answers
- View conversation history per agent

Stack options:
- **Terminal**: Rich (Python) for a polished TUI
- **Web**: FastAPI + minimal HTML/JS frontend with SSE for streaming

### 4. Security Testing
Demonstrate BeeAI's guardrails and where they kick in:
- **Prompt injection**: send adversarial instructions hidden in tool output and show the agent resists hijacking
- **Jailbreak attempts**: try common jailbreak prompts and show how a well-configured system prompt holds up
- **Tool abuse**: attempt to call tools with malicious arguments (e.g., code injection in `calculate`) and show input validation blocking it
- **Data leakage**: ask an agent to reveal its system prompt and show it refuses

Document each test case with: input, expected behavior, actual behavior.

---

## Suggested Project Structure

```
beeai-fase-three/
├── planning.md          # this file
├── agents/
│   ├── assistant.py     # assistant personality config
│   ├── creative.py      # creative personality config
│   └── critic.py        # critic personality config
├── tools/
│   ├── weather.py
│   ├── search.py
│   ├── calculator.py
│   └── summarizer.py
├── app/
│   ├── main.py          # entry point (TUI or web)
│   └── ui.py            # rendering / interface logic
├── security/
│   └── tests.py         # prompt injection and jailbreak test cases
└── requirements.txt
```

---

## Key BeeAI Concepts to Highlight

| Concept | Where it shows up |
|---|---|
| Agent personality | Multi-agent chat demo |
| Tool / function calling | Weather, search, calculator tools |
| Streaming output | Real-time reply rendering in UI |
| Multi-agent orchestration | Summarizer tool calls a second agent |
| Safety / guardrails | Security test suite |

---

## Open Questions
- Use BeeAI's built-in memory or keep stateless for simplicity?
- Real external APIs (weather, search) or mock everything for offline demo?
- TUI (simpler, no deps) vs web UI (more impressive visually)?
