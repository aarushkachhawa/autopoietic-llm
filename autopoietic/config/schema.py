from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    path: str = "mlx-community/Qwen2.5-1.5B-Instruct-4bit"
    adapter_path: str | None = None
    max_tokens: int = 512
    temp: float = 0.2


class TaskConfig(BaseModel):
    task_set: str = "coding_katas"
    max_turns: int = 10


class RootConfig(BaseModel):
    data_dir: Path = Path("data")
    model: ModelConfig = Field(default_factory=ModelConfig)
    task: TaskConfig = Field(default_factory=TaskConfig)
