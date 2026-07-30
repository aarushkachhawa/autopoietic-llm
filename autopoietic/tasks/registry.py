from __future__ import annotations

from pathlib import Path
from typing import Callable

from autopoietic.core.task import Task
from autopoietic.tasks.coding_katas.task import CodingKataTask, load_katas

KATAS_DIR = Path(__file__).parent / "coding_katas" / "katas"


def build_coding_kata_tasks(max_turns: int = 10) -> list[Task]:
    return [CodingKataTask(spec, max_turns=max_turns) for spec in load_katas(KATAS_DIR)]


TASK_SET_BUILDERS: dict[str, Callable[..., list[Task]]] = {
    "coding_katas": build_coding_kata_tasks,
}


def build_task_set(name: str, max_turns: int = 10) -> list[Task]:
    if name not in TASK_SET_BUILDERS:
        raise ValueError(f"unknown task set '{name}', available: {sorted(TASK_SET_BUILDERS)}")
    return TASK_SET_BUILDERS[name](max_turns=max_turns)
