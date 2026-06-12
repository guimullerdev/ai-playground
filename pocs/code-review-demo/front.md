# Frontend Plan — Vanilla HTML/JS

Single file: `index.html`. No build step, no framework, no dependencies. Served statically — open directly in browser or via any HTTP server.

---

## Layout

```
┌──────────────────────────────────────────────────────┐
│  Code Review Demo                                    │
├──────────────────┬───────────────────────────────────┤
│                  │  AGENT STREAM                     │
│  [textarea]      │  ┌────────────────────────────┐  │
│                  │  │ 🟢 orchestrator             │  │
│  Paste code      │  │   Starting review pipeline  │  │
│  here            │  ├────────────────────────────┤  │
│                  │  │ 🔵 dev                      │  │
│                  │  │   💭 Thinking...             │  │
│                  │  ├────────────────────────────┤  │
│                  │  │ 🔴 security (CRITICAL)      │  │
│  [Run Review]    │  │   SQL injection via f-string│  │
│                  │  └────────────────────────────┘  │
│                  │                                   │
│                  │  ┌────────────────────────────┐  │
│                  │  │ 👤 Human approval needed    │  │
│                  │  │  [Approve]  [Reject]        │  │  ← shown only on human_approval event
│                  │  └────────────────────────────┘  │
│                  │                                   │
│                  │  ┌────────────────────────────┐  │
│                  │  │ VERDICT: BLOCKED            │  │  ← shown only on verdict event
│                  │  └────────────────────────────┘  │
└──────────────────┴───────────────────────────────────┘
```

---

## Files

```
code-review-demo/
└── index.html      ← single file, everything inline
```

---

## WebSocket Event Handling

| Event type       | What to render                                                       |
|------------------|----------------------------------------------------------------------|
| `agent.start`    | New agent section header in the stream                               |
| `agent.thinking` | Indented line prefixed with 💭, dimmed text                          |
| `agent.handoff`  | "→ handing off to X" line                                            |
| `tool.start`     | "⚙ using tool: X" line, dimmed                                       |
| `tool.end`       | Append tool result inline, collapsed by default                      |
| `finding`        | Bold line, color-coded by severity (🔴 critical / 🟡 warning / ℹ️ info) |
| `human_approval` | Show approval banner with Approve / Reject buttons                   |
| `verdict`        | Show final verdict box (APPROVED / CHANGES_REQUESTED / BLOCKED)      |

Severity colors:
- `critical` → red (`#ff4d4d`)
- `warning` → amber (`#ffaa00`)
- `info` → blue (`#4d9fff`)
- `null` → default text

---

## Connection & State Machine

```
IDLE
  │ user clicks "Run Review"
  ▼
CONNECTING  → open WebSocket to ws://localhost:8000/ws
  │ WS open
  ▼
REVIEWING   → POST /review { code }
  │          → stream events into the log
  │ human_approval event
  ▼
AWAITING_APPROVAL  → show Approve/Reject buttons
  │ user clicks Approve or Reject
  ▼
POST /approve { approved: true|false }
  │
  ▼
DONE  → render verdict box, close WS
```

Button states:
- "Run Review" is disabled while `REVIEWING` or `AWAITING_APPROVAL`
- Approve/Reject buttons are hidden except during `AWAITING_APPROVAL`

---

## Implementation Notes

- All styles inline in `<style>` — dark theme, monospace font for the stream
- All logic in a single `<script>` block at the bottom of `<body>`
- Backend URL configurable via a `const BASE_URL = 'http://localhost:8000'` at the top of the script
- Auto-scroll the stream panel to the bottom on each new event
- Textarea pre-filled with the sample broken code from `plan.md` for quick demo
- No external fonts, icons, or CDN links — purely self-contained

---

## Sample pre-fill (textarea default)

```python
def authenticate(username, password):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    result = db.execute(query)
    eval(result["callback"])
    return result
```

---

## Implementation Order

| Step | What |
|------|------|
| 1 | HTML skeleton: two-column layout, textarea, stream panel |
| 2 | WebSocket connection + event dispatch loop |
| 3 | Render functions per event type |
| 4 | State machine: button enable/disable, approval banner visibility |
| 5 | Verdict box styling |
| 6 | Polish: auto-scroll, pre-fill, dark theme |
