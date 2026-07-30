from __future__ import annotations

import json
import re
from typing import Any

from autopoietic.agent.prompting import ACTION_FENCE
from autopoietic.core.task import Task, ToolResult

_ACTION_RE = re.compile(r"```" + re.escape(ACTION_FENCE) + r"\s*\n(.*?)```", re.DOTALL)


class ActionParseError(Exception):
    pass


def parse_action(text: str) -> tuple[str, dict[str, Any]]:
    """Extract the last ```action fenced block from assistant text. Taking
    the last (not first) block lets the model reason first and self-correct
    within a single turn before committing to an action."""
    matches = _ACTION_RE.findall(text)
    if not matches:
        raise ActionParseError("no ```action block found")
    raw = matches[-1].strip()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ActionParseError(f"action block is not valid JSON: {e}") from e
    if "tool" not in payload:
        raise ActionParseError("action JSON missing 'tool' key")
    return payload["tool"], payload.get("args", {})


def execute_action(task: Task, tool_name: str, args: dict[str, Any]) -> ToolResult:
    valid_names = {t.name for t in task.tools()}
    if tool_name not in valid_names:
        return ToolResult(
            success=False,
            output=f"unknown tool '{tool_name}', valid tools: {sorted(valid_names)}",
        )
    return task.handle_tool_call(tool_name, args)
