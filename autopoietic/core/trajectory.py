from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from autopoietic.core.grader import GradeResult
from autopoietic.core.types import Outcome


class Message(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_name: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Trajectory(BaseModel):
    trajectory_id: str
    task_id: str
    task_domain: str
    adapter_version: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    messages: list[Message]
    outcome: Outcome
    grade: GradeResult
    metadata: dict[str, Any] = {}
