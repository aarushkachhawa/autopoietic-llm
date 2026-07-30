from __future__ import annotations

from pathlib import Path

from autopoietic.core.trajectory import Trajectory
from autopoietic.core.types import Outcome
from autopoietic.storage.db import connect


class TrajectoryStore:
    """Append-only JSONL per day + a SQLite index for fast filtering,
    without scanning every JSONL file on every query."""

    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.conn = connect(self.root / "trajectories.db")
        self._line_counts: dict[Path, int] = {}

    def _jsonl_path_for(self, trajectory: Trajectory) -> Path:
        return self.root / f"{trajectory.created_at.strftime('%Y-%m-%d')}.jsonl"

    def _line_count(self, path: Path) -> int:
        if path not in self._line_counts:
            self._line_counts[path] = sum(1 for _ in open(path)) if path.exists() else 0
        return self._line_counts[path]

    def append(self, trajectory: Trajectory) -> None:
        path = self._jsonl_path_for(trajectory)
        line_no = self._line_count(path)
        with open(path, "a") as f:
            f.write(trajectory.model_dump_json() + "\n")
        self._line_counts[path] = line_no + 1

        self.conn.execute(
            "INSERT OR REPLACE INTO trajectories "
            "(id, task_id, task_domain, outcome, score, adapter_version, created_at, file_path, line_no) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                trajectory.trajectory_id,
                trajectory.task_id,
                trajectory.task_domain,
                trajectory.outcome.value,
                trajectory.grade.score,
                trajectory.adapter_version,
                trajectory.created_at.isoformat(),
                path.name,
                line_no,
            ),
        )
        self.conn.commit()

    def query(
        self,
        domain: str | None = None,
        outcome: Outcome | None = None,
        adapter_version: str | None = None,
    ) -> list[Trajectory]:
        clauses = []
        params: list[str] = []
        if domain is not None:
            clauses.append("task_domain = ?")
            params.append(domain)
        if outcome is not None:
            clauses.append("outcome = ?")
            params.append(outcome.value)
        if adapter_version is not None:
            clauses.append("adapter_version = ?")
            params.append(adapter_version)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self.conn.execute(
            f"SELECT file_path, line_no FROM trajectories {where}", params
        ).fetchall()

        by_file: dict[str, set[int]] = {}
        for file_path, line_no in rows:
            by_file.setdefault(file_path, set()).add(line_no)

        out: list[Trajectory] = []
        for file_path, wanted in by_file.items():
            with open(self.root / file_path) as f:
                for i, line in enumerate(f):
                    if i in wanted:
                        out.append(Trajectory.model_validate_json(line))
        return out
