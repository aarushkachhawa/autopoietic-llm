import json

from autopoietic.agent.loop import run_episode
from autopoietic.core.trajectory import Message
from autopoietic.core.types import Outcome
from autopoietic.tasks.coding_katas.grader import PytestGrader
from autopoietic.tasks.coding_katas.task import CodingKataTask, load_katas
from autopoietic.tasks.registry import KATAS_DIR

FIZZBUZZ_SOLUTION = (
    "def fizzbuzz(n):\n"
    "    out = []\n"
    "    for i in range(1, n + 1):\n"
    '        if i % 15 == 0:\n'
    '            out.append("FizzBuzz")\n'
    "        elif i % 3 == 0:\n"
    '            out.append("Fizz")\n'
    "        elif i % 5 == 0:\n"
    '            out.append("Buzz")\n'
    "        else:\n"
    "            out.append(str(i))\n"
    "    return out\n"
)


class ScriptedChatClient:
    """Fake ChatClient returning a fixed sequence of replies, used to test
    the agent loop's wiring without needing mlx-lm or a downloaded model."""

    def __init__(self, replies: list[str]):
        self._replies = list(replies)

    def generate(self, messages: list[Message]) -> str:
        return self._replies.pop(0)


def _action(tool: str, args: dict) -> str:
    return f"```action\n{json.dumps({'tool': tool, 'args': args})}\n```"


def _fizzbuzz_task(max_turns: int = 5) -> CodingKataTask:
    spec = next(s for s in load_katas(KATAS_DIR) if s.id == "fizzbuzz")
    return CodingKataTask(spec, max_turns=max_turns)


def test_successful_episode_end_to_end():
    task = _fizzbuzz_task()
    client = ScriptedChatClient(
        [
            _action("write_file", {"content": FIZZBUZZ_SOLUTION}),
            _action("submit", {}),
        ]
    )

    trajectory = run_episode(task, client, PytestGrader())

    assert trajectory.outcome == Outcome.SUCCESS
    assert trajectory.grade.passed
    assert trajectory.task_id == "fizzbuzz"
    assert trajectory.metadata["num_turns"] == 2


def test_invalid_action_nudges_then_recovers():
    task = _fizzbuzz_task()
    client = ScriptedChatClient(
        [
            "Let me think about this problem first.",  # no action block
            _action("write_file", {"content": FIZZBUZZ_SOLUTION}),
            _action("submit", {}),
        ]
    )

    trajectory = run_episode(task, client, PytestGrader())

    assert trajectory.outcome == Outcome.SUCCESS
    tool_messages = [m for m in trajectory.messages if m.role == "tool"]
    assert any("No valid action found" in m.content for m in tool_messages)


def test_never_submitting_hits_max_turns_and_fails():
    task = _fizzbuzz_task(max_turns=2)
    client = ScriptedChatClient(
        [
            _action("write_file", {"content": FIZZBUZZ_SOLUTION}),
            _action("run_tests", {}),
        ]
    )

    trajectory = run_episode(task, client, PytestGrader())

    assert trajectory.outcome == Outcome.FAILURE
    assert trajectory.grade.detail["reason"] == "not submitted"


def test_adapter_version_is_recorded_on_trajectory():
    task = _fizzbuzz_task()
    client = ScriptedChatClient([_action("submit", {})])

    trajectory = run_episode(task, client, PytestGrader(), adapter_version="v3")

    assert trajectory.adapter_version == "v3"
