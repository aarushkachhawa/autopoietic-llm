from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS trajectories (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    task_domain TEXT NOT NULL,
    outcome TEXT NOT NULL,
    score REAL NOT NULL,
    adapter_version TEXT,
    created_at TEXT NOT NULL,
    file_path TEXT NOT NULL,
    line_no INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_traj_domain_outcome ON trajectories(task_domain, outcome);
CREATE INDEX IF NOT EXISTS idx_traj_adapter ON trajectories(adapter_version);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    return conn
