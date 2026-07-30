from __future__ import annotations

import time
import uuid

from autopoietic.agent.llm_client import ChatClient
from autopoietic.agent.prompting import build_system_prompt
from autopoietic.agent.tools import ActionParseError, execute_action, parse_action
from autopoietic.core.grader import Grader
from autopoietic.core.task import Task
from autopoietic.core.trajectory import Message, Trajectory
from autopoietic.core.types import Outcome

NO_ACTION_NUDGE = (
    "No valid action found in your last response. Every turn must end with "
    "exactly one ```action``` block calling one of the available tools."
)


def _resolve_outcome(grade) -> Outcome:
    if grade.passed:
        return Outcome.SUCCESS
    if grade.detail.get("timeout"):
        return Outcome.TIMEOUT
    if grade.detail.get("error"):
        return Outcome.ERROR
    return Outcome.FAILURE


def run_episode(
    task: Task,
    chat_client: ChatClient,
    grader: Grader,
    adapter_version: str | None = None,
) -> Trajectory:
    messages: list[Message] = [
        Message(role="system", content=build_system_prompt(task)),
        Message(role="user", content=task.initial_user_message()),
    ]

    start = time.monotonic()
    num_turns = 0
    for _turn in range(task.max_turns):
        num_turns += 1
        reply = chat_client.generate(messages)
        messages.append(Message(role="assistant", content=reply))

        try:
            tool_name, args = parse_action(reply)
        except ActionParseError:
            messages.append(Message(role="tool", content=NO_ACTION_NUDGE))
            continue

        result = execute_action(task, tool_name, args)
        messages.append(Message(role="tool", tool_name=tool_name, content=result.output))

        if task.is_terminal(messages):
            break

    grade = grader.grade(task, messages)
    outcome = _resolve_outcome(grade)

    return Trajectory(
        trajectory_id=str(uuid.uuid4()),
        task_id=task.task_id,
        task_domain=task.domain,
        adapter_version=adapter_version,
        messages=messages,
        outcome=outcome,
        grade=grade,
        metadata={
            "num_turns": num_turns,
            "wall_clock_s": time.monotonic() - start,
        },
    )
