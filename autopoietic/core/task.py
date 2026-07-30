from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

if TYPE_CHECKING:
    from autopoietic.core.trajectory import Message


class ToolSpec(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]


class ToolResult(BaseModel):
    success: bool
    output: str


class Task(ABC):
    """Domain-agnostic episode definition. The agent loop only ever calls
    these methods plus a ChatClient, so a new domain plugs in without
    touching agent/loop.py, storage, curation, or training code."""

    def __init__(self, task_id: str, domain: str, max_turns: int = 10):
        self.task_id = task_id
        self.domain = domain
        self.max_turns = max_turns

    @abstractmethod
    def system_prompt(self) -> str: ...

    @abstractmethod
    def initial_user_message(self) -> str: ...

    @abstractmethod
    def tools(self) -> list[ToolSpec]: ...

    @abstractmethod
    def handle_tool_call(self, name: str, args: dict[str, Any]) -> ToolResult: ...

    @abstractmethod
    def is_terminal(self, messages: list["Message"]) -> bool: ...
