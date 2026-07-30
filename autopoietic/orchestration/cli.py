from __future__ import annotations

from pathlib import Path

import typer

from autopoietic.agent.llm_client import MLXClient
from autopoietic.agent.loop import run_episode
from autopoietic.config.loader import load_config
from autopoietic.core.types import Outcome
from autopoietic.storage.trajectory_store import TrajectoryStore
from autopoietic.tasks.coding_katas.grader import PytestGrader
from autopoietic.tasks.registry import build_task_set

app = typer.Typer(help="autopoietic-llm: a self-evolving agent flywheel")


@app.callback()
def _main() -> None:
    """autopoietic-llm: a self-evolving agent flywheel.

    Forces subcommand syntax (`autopoietic run-tasks ...`) even while
    run-tasks is the only command - Typer otherwise flattens a single-command
    app and drops the subcommand name, which would break once curate/train/
    eval/promote/cycle are added in later milestones.
    """


@app.command("run-tasks")
def run_tasks(
    config: list[Path] = typer.Option(
        [Path("configs/base.yaml")], "--config", "-c", help="Config file(s), later ones override earlier ones"
    ),
    task_set: str = typer.Option(None, help="Override task.task_set from config"),
    n: int = typer.Option(5, help="Number of episodes to run"),
    adapter_path: str = typer.Option(None, help="Override model.adapter_path"),
) -> None:
    """Run N episodes against the configured task set and log trajectories."""
    cfg = load_config(config)
    if task_set:
        cfg.task.task_set = task_set
    if adapter_path:
        cfg.model.adapter_path = adapter_path

    tasks = build_task_set(cfg.task.task_set, max_turns=cfg.task.max_turns)
    if not tasks:
        typer.echo(f"no tasks found for task set '{cfg.task.task_set}'")
        raise typer.Exit(1)

    typer.echo(f"loading model {cfg.model.path} (adapter={cfg.model.adapter_path})...")
    client = MLXClient(
        cfg.model.path,
        adapter_path=cfg.model.adapter_path,
        max_tokens=cfg.model.max_tokens,
        temp=cfg.model.temp,
    )
    grader = PytestGrader()
    store = TrajectoryStore(cfg.data_dir / "trajectories")

    n_success = 0
    for i in range(n):
        # Rebuild fresh task instances each episode: Task instances are
        # mutable per-episode state (e.g. submitted flag), so reusing one
        # across episodes would leak state from a prior run.
        episode_tasks = build_task_set(cfg.task.task_set, max_turns=cfg.task.max_turns)
        task = episode_tasks[i % len(episode_tasks)]

        trajectory = run_episode(task, client, grader, adapter_version=cfg.model.adapter_path)
        store.append(trajectory)

        if trajectory.outcome == Outcome.SUCCESS:
            n_success += 1
        typer.echo(
            f"[{i + 1}/{n}] task={task.task_id} outcome={trajectory.outcome.value} "
            f"score={trajectory.grade.score:.2f} turns={trajectory.metadata['num_turns']}"
        )

    typer.echo(f"\n{n_success}/{n} episodes succeeded ({n_success / n:.0%})")


if __name__ == "__main__":
    app()
