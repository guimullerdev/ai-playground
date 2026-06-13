import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from opentelemetry import trace
from pydantic import BaseModel

from agents.dev_agent import create_dev_agent
from agents.security_agent import create_security_agent
from agents.perf_agent import create_perf_agent
from agents.lead_agent import create_lead_agent, run_lead_with_approval
from agents.orchestrator import create_orchestrator
from core.event_bridge import attach_bridge
from core.models import ReviewEvent
from core.telemetry import setup_telemetry

app = FastAPI()
setup_telemetry(app)

tracer = trace.get_tracer("code-review-demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/ui", StaticFiles(directory="ui"), name="ui")


@app.get("/")
async def root():
    return FileResponse("ui/index.html")

_active_ws: WebSocket | None = None
_approval_event: asyncio.Event = asyncio.Event()


class ReviewRequest(BaseModel):
    code: str


class ApprovalRequest(BaseModel):
    approved: bool


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    global _active_ws
    await ws.accept()
    _active_ws = ws
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        _active_ws = None


@app.post("/review")
async def start_review(req: ReviewRequest):
    _approval_event.clear()
    asyncio.create_task(_run_pipeline(req.code))
    return {"status": "started"}


@app.post("/approve")
async def approve(req: ApprovalRequest):
    if req.approved:
        _approval_event.set()
    return {"status": "ok"}


async def _ws_send(message: str) -> None:
    if _active_ws:
        await _active_ws.send_text(message)


async def _run_pipeline(code: str) -> None:
    with tracer.start_as_current_span("review.pipeline") as pipeline_span:
        pipeline_span.set_attribute("code.length", len(code))

        dev = create_dev_agent()
        security = create_security_agent()
        perf = create_perf_agent()
        lead = create_lead_agent()
        orchestrator = create_orchestrator(dev, security, perf)

        for agent, name in [(orchestrator, "orchestrator"), (dev, "dev"), (security, "security"), (perf, "perf")]:
            await attach_bridge(agent, _ws_send, name)

        await _ws_send(ReviewEvent(type="agent.start", agent="orchestrator", message="Starting review pipeline", severity=None).to_json())

        with tracer.start_as_current_span("agent.orchestrator"):
            result = await orchestrator.run(f"Review this code:\n\n{code}")
        findings = result.output.text

        await _ws_send(ReviewEvent(type="agent.start", agent="lead", message="Consolidating findings", severity=None).to_json())
        await attach_bridge(lead, _ws_send, "lead")

        with tracer.start_as_current_span("agent.lead"):
            verdict = await run_lead_with_approval(lead, findings, _ws_send, _approval_event)

        pipeline_span.set_attribute("review.verdict", verdict)
        await _ws_send(ReviewEvent(type="verdict", agent="lead", message=verdict, severity=None).to_json())
