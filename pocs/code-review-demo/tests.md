# Unit Tests Plan

## Goals

- Cover all pure logic without hitting the real LLM or BeeAI runtime
- Keep tests fast and hermetic — every external dependency is mocked
- Use `pytest` + `pytest-asyncio` throughout; `FastAPI TestClient` for HTTP/WebSocket endpoints

---

## New dependencies

```txt
# add to requirements.txt
pytest
pytest-asyncio
httpx          # required by FastAPI TestClient for async
```

---

## Folder structure

```
tests/
├── __init__.py
├── conftest.py             # shared fixtures (mock LLM, mock agent, mock ws_send)
├── test_models.py
├── test_event_bridge.py
├── test_backend.py
├── test_telemetry.py
├── test_agents.py
├── test_lead_agent.py
└── test_server.py
```

---

## Shared fixtures (`conftest.py`)

| Fixture | What it provides |
|---------|-----------------|
| `mock_llm` | `MagicMock` standing in for `ChatModel`; patches `core.backend.ChatModel` |
| `mock_agent` | Object with `.emitter.on()` and async `.run()` returning a fake result |
| `ws_send` | `AsyncMock` that records every string it receives |
| `approval_event` | Real `asyncio.Event`, pre-cleared |

---

## Test files

### `test_models.py` — `ReviewEvent`

| Test | What it checks |
|------|---------------|
| `test_to_json_roundtrip` | `json.loads(evt.to_json())` contains all fields |
| `test_timestamp_auto_set` | `timestamp` is populated when not passed |
| `test_timestamp_explicit` | Explicit `timestamp` is preserved |
| `test_all_event_types` | Every `type` literal is accepted without error |
| `test_severity_none` | `severity=None` serializes to `null` |

---

### `test_event_bridge.py` — `_map_event`

`_map_event` is a pure function — no mocks needed.

| Test | Input `event_name` | Expected `type` |
|------|--------------------|----------------|
| `test_think_event` | `"agent.think.start"` | `agent.thinking` |
| `test_tool_start_event` | `"tool.call.start"` | `tool.start` |
| `test_tool_end_event` | `"tool.call.end"` | `tool.end` |
| `test_unknown_event_returns_none` | `"agent.start"` | `None` |
| `test_message_includes_agent_name` | any think event | `agent` field matches passed name |

Also test `attach_bridge`:

| Test | What it checks |
|------|---------------|
| `test_attach_bridge_registers_handler` | `agent.emitter.on("*.*")` is called once |
| `test_attach_bridge_calls_ws_send` | simulated emitter fires → `ws_send` receives JSON |

---

### `test_backend.py` — `get_llm`

| Test | What it checks |
|------|---------------|
| `test_default_model_name` | No env var → model name contains `claude-3.5-haiku` |
| `test_custom_model_from_env` | `OPENAI_CHAT_MODEL=gpt-4o` → model name contains `gpt-4o` |
| `test_returns_chat_model_instance` | Return value is a `ChatModel` (mock verified) |

All tests patch `ChatModel.from_name` to avoid real network calls.

---

### `test_telemetry.py` — `setup_telemetry`

| Test | What it checks |
|------|---------------|
| `test_no_op_without_endpoint` | Unset `OTEL_EXPORTER_OTLP_ENDPOINT` → `TracerProvider` is NOT configured |
| `test_configures_provider_with_endpoint` | Env set → `trace.get_tracer_provider()` is a `TracerProvider` |
| `test_fastapi_instrumented` | `FastAPIInstrumentor.instrument_app` is called once |
| `test_httpx_instrumented` | `HTTPXClientInstrumentor().instrument` is called once |
| `test_service_name_default` | No `OTEL_SERVICE_NAME` → resource has `code-review-demo` |
| `test_service_name_from_env` | Custom name env var → resource reflects it |

Patch `OTLPSpanExporter`, `FastAPIInstrumentor`, `HTTPXClientInstrumentor` to avoid network.

---

### `test_agents.py` — factory functions

Each `create_*_agent()` is tested for its **configuration**, not its runtime behaviour.
All tests patch `get_llm` to return `mock_llm`.

#### Dev agent

| Test | What it checks |
|------|---------------|
| `test_dev_agent_has_think_tool` | `ThinkTool` is in `tools` |
| `test_dev_agent_has_conditional_requirement` | `ConditionalRequirement` with `force_at_step=1` |
| `test_dev_agent_role` | `role == "dev_reviewer"` |

#### Security agent

| Test | What it checks |
|------|---------------|
| `test_security_agent_has_two_requirements` | Two `ConditionalRequirement` entries |
| `test_security_agent_force_at_step_1` | First requirement forces think at step 1 |
| `test_security_agent_force_after_tool` | Second requirement has `force_after=Tool` |
| `test_security_agent_role` | `role == "security_reviewer"` |

#### Perf agent

| Test | What it checks |
|------|---------------|
| `test_perf_agent_has_think_tool` | `ThinkTool` is in `tools` |
| `test_perf_agent_has_memory` | `UnconstrainedMemory` is set |
| `test_perf_agent_role` | `role == "performance_reviewer"` |

#### Orchestrator

| Test | What it checks |
|------|---------------|
| `test_orchestrator_has_three_handoff_tools` | Exactly 3 `HandoffTool` instances in `tools` |
| `test_orchestrator_handoff_names` | Tool names are `handoff_dev`, `handoff_security`, `handoff_perf` |
| `test_orchestrator_role` | `role == "orchestrator"` |

---

### `test_lead_agent.py` — `run_lead_with_approval`

All tests use `mock_agent`, `ws_send`, and `approval_event` fixtures.

| Test | What it checks |
|------|---------------|
| `test_emits_human_approval_event` | `ws_send` receives a JSON with `type == "human_approval"` |
| `test_waits_for_approval_event` | `approval_event` not set → coroutine does not return (timeout guard) |
| `test_resumes_after_approval` | Set `approval_event` → `lead_agent.run()` is called |
| `test_returns_agent_output` | Return value matches `mock_agent.run().output.text` |
| `test_approval_event_agent_field` | `human_approval` JSON has `agent == "lead"` |

---

### `test_server.py` — FastAPI endpoints

Use `httpx.AsyncClient` with `ASGITransport` for full async TestClient.
Patch `_run_pipeline` so no real agents are created.

#### HTTP endpoints

| Test | What it checks |
|------|---------------|
| `test_get_root_returns_html` | `GET /` → 200, `Content-Type: text/html` |
| `test_post_review_starts_pipeline` | `POST /review` → `{"status": "started"}` |
| `test_post_review_spawns_task` | `_run_pipeline` mock is called with the submitted code |
| `test_post_approve_sets_event` | `POST /approve {"approved": true}` → `_approval_event.is_set()` |
| `test_post_approve_false_does_not_set` | `approved: false` → event stays unset |
| `test_post_approve_returns_ok` | Response body is `{"status": "ok"}` |

#### WebSocket endpoint

| Test | What it checks |
|------|---------------|
| `test_ws_accepts_connection` | Client can connect to `/ws` without error |
| `test_ws_receives_sent_message` | After connecting, `_ws_send("hello")` delivers the message to the client |
| `test_ws_disconnect_clears_active_ws` | Client disconnects → `_active_ws` becomes `None` |

---

## Implementation order

| Step | File | Effort |
|------|------|--------|
| 1 | `tests/__init__.py` + `conftest.py` | Shared fixtures, verify pytest runs |
| 2 | `test_models.py` | Pure dataclass — fastest win |
| 3 | `test_event_bridge.py` | Pure function + one async test |
| 4 | `test_backend.py` | Env var patching |
| 5 | `test_agents.py` | Factory config assertions |
| 6 | `test_telemetry.py` | Provider + middleware mocks |
| 7 | `test_lead_agent.py` | Async flow with event gating |
| 8 | `test_server.py` | TestClient + WebSocket |

---

## pytest configuration (`pytest.ini` or `pyproject.toml`)

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
```
