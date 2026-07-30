from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from autopoietic.core.task import Task, ToolResult, ToolSpec
from autopoietic.core.trajectory import Message

DOMAIN = "coding_katas"


@dataclass
class KataSpec:
    id: str
    prompt: str
    difficulty: str
    tags: list[str]
    test_file: Path
    starter_code: str = ""

    @classmethod
    def load(cls, kata_dir: Path) -> "KataSpec":
        with open(kata_dir / "task.yaml") as f:
            raw = yaml.safe_load(f)
        test_files = sorted(kata_dir.glob("test_*.py"))
        if not test_files:
            raise FileNotFoundError(f"no test_*.py found in {kata_dir}")
        starter_path = kata_dir / "starter_code.py"
        starter_code = starter_path.read_text() if starter_path.exists() else ""
        return cls(
            id=raw["id"],
            prompt=raw["prompt"],
            difficulty=raw.get("difficulty", "unknown"),
            tags=raw.get("tags", []),
            test_file=test_files[0],
            starter_code=starter_code,
        )


def load_katas(katas_dir: Path) -> list[KataSpec]:
    return [
        KataSpec.load(d)
        for d in sorted(katas_dir.iterdir())
        if d.is_dir() and (d / "task.yaml").exists()
    ]


class CodingKataTask(Task):
    """One episode of solving a single kata. write_file sets the candidate
    solution; run_tests is a cheap syntax smoke-check only (the hidden
    grading tests never run inside the agent's own sandbox, only via
    PytestGrader after submit); submit ends the episode."""

    def __init__(self, spec: KataSpec, max_turns: int = 10):
        super().__init__(task_id=spec.id, domain=DOMAIN, max_turns=max_turns)
        self.spec = spec
        self.solution_code = spec.starter_code
        self.submitted = False

    def system_prompt(self) -> str:
        return (
            "You are solving a small Python coding kata. Write a single "
            "solution.py file containing the requested function(s), then submit."
        )

    def initial_user_message(self) -> str:
        return self.spec.prompt

    def tools(self) -> list[ToolSpec]:
        return [
            ToolSpec(
                name="write_file",
                description="Overwrite solution.py with the given content.",
                parameters={"content": "string, the full contents of solution.py"},
            ),
            ToolSpec(
                name="run_tests",
                description=(
                    "Check that the current solution.py compiles (syntax only, "
                    "does not run the hidden grading tests)."
                ),
                parameters={},
            ),
            ToolSpec(
                name="submit",
                description="Finalize solution.py for grading and end the episode.",
                parameters={},
            ),
        ]

    def handle_tool_call(self, name: str, args: dict[str, Any]) -> ToolResult:
        if name == "write_file":
            content = args.get("content", "")
            if not isinstance(content, str) or not content.strip():
                return ToolResult(success=False, output="content must be a non-empty string")
            self.solution_code = content
            return ToolResult(success=True, output="solution.py written")

        if name == "run_tests":
            try:
                compile(self.solution_code, "solution.py", "exec")
            except SyntaxError as e:
                return ToolResult(success=False, output=f"SyntaxError: {e}")
            return ToolResult(success=True, output="solution.py compiles cleanly")

        if name == "submit":
            self.submitted = True
            return ToolResult(success=True, output="submitted, awaiting grading")

        return ToolResult(success=False, output=f"unhandled tool '{name}'")

    def is_terminal(self, messages: list[Message]) -> bool:
        return self.submitted
