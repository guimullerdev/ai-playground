from dataclasses import dataclass, asdict
from typing import Literal
import time
import json


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
        "verdict",
    ]
    agent: str           # "orchestrator" | "dev" | "security" | "perf" | "lead"
    message: str         # text for the thought stream
    severity: str | None # "critical" | "warning" | "info" | None
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

    def to_json(self) -> str:
        return json.dumps(asdict(self))
