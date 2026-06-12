from typing import Callable, Awaitable
from core.models import ReviewEvent


async def attach_bridge(agent, ws_send: Callable[[str], Awaitable[None]], agent_name: str) -> None:
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
