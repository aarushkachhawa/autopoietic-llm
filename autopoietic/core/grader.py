from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

if TYPE_CHECKING:
    from autopoietic.core.task import Task
    from autopoietic.core.trajectory import Message


class GradeResult(BaseModel):
    passed: bool
    score: float
    detail: dict[str, Any] = {}


class Grader(ABC):
    """Grades the final state of an episode. Takes the raw message history
    rather than a Trajectory, since Trajectory embeds a GradeResult and is
    only constructed *after* grading completes."""

    @abstractmethod
    def grade(self, task: "Task", messages: list["Message"]) -> GradeResult: ...
