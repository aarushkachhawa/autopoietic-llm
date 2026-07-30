from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from autopoietic.core.grader import GradeResult, Grader
from autopoietic.core.trajectory import Message
from autopoietic.tasks.coding_katas.task import CodingKataTask

_PASSED_RE = re.compile(r"(\d+) passed")
_FAILED_RE = re.compile(r"(\d+) failed")
_ERROR_RE = re.compile(r"(\d+) error")


def _count(pattern: re.Pattern, text: str) -> int:
    m = pattern.search(text)
    return int(m.group(1)) if m else 0


class PytestGrader(Grader):
    """Runs a kata's hidden test_*.py against the agent's submitted
    solution.py, in an isolated tmp dir, as a subprocess with a wall-clock
    timeout. Fully CPU-only, independent of any LLM."""

    def __init__(self, timeout_s: float = 10.0):
        self.timeout_s = timeout_s

    def grade(self, task: CodingKataTask, messages: list[Message]) -> GradeResult:
        if not task.submitted:
            return GradeResult(passed=False, score=0.0, detail={"reason": "not submitted"})

        with tempfile.TemporaryDirectory(prefix="autopoietic-kata-") as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "solution.py").write_text(task.solution_code)
            shutil.copy(task.spec.test_file, tmp_path / task.spec.test_file.name)

            try:
                proc = subprocess.run(
                    [sys.executable, "-m", "pytest", "-q", "--tb=short", "-p", "no:cacheprovider"],
                    cwd=tmp_path,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_s,
                )
            except subprocess.TimeoutExpired as e:
                return GradeResult(
                    passed=False,
                    score=0.0,
                    detail={"timeout": True, "stdout": e.stdout or "", "stderr": e.stderr or ""},
                )

            output = proc.stdout + proc.stderr
            passed_n = _count(_PASSED_RE, output)
            failed_n = _count(_FAILED_RE, output)
            error_n = _count(_ERROR_RE, output)
            total = passed_n + failed_n + error_n

            if total == 0:
                return GradeResult(
                    passed=False,
                    score=0.0,
                    detail={"error": "could not parse pytest output", "stdout": output},
                )

            score = passed_n / total
            return GradeResult(
                passed=proc.returncode == 0 and failed_n == 0 and error_n == 0,
                score=score,
                detail={
                    "tests_passed": passed_n,
                    "tests_failed": failed_n,
                    "tests_errored": error_n,
                    "returncode": proc.returncode,
                    "stdout": output,
                },
            )
