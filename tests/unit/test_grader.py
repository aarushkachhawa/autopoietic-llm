from autopoietic.tasks.coding_katas.grader import PytestGrader
from autopoietic.tasks.coding_katas.task import CodingKataTask, load_katas
from autopoietic.tasks.registry import KATAS_DIR

GCD_CORRECT = "def gcd(a, b):\n    while b:\n        a, b = b, a % b\n    return a\n"
GCD_WRONG = "def gcd(a, b):\n    return 42\n"
GCD_HANGS = "def gcd(a, b):\n    while True:\n        pass\n"


def _kata_task(kata_id: str) -> CodingKataTask:
    spec = next(s for s in load_katas(KATAS_DIR) if s.id == kata_id)
    return CodingKataTask(spec)


def test_grades_correct_solution_as_passed():
    task = _kata_task("gcd")
    task.solution_code = GCD_CORRECT
    task.submitted = True

    result = PytestGrader().grade(task, [])

    assert result.passed
    assert result.score == 1.0
    assert result.detail["tests_failed"] == 0


def test_grades_wrong_solution_as_failed():
    task = _kata_task("gcd")
    task.solution_code = GCD_WRONG
    task.submitted = True

    result = PytestGrader().grade(task, [])

    assert not result.passed
    assert 0.0 <= result.score < 1.0


def test_not_submitted_short_circuits_without_running_pytest():
    task = _kata_task("gcd")

    result = PytestGrader().grade(task, [])

    assert not result.passed
    assert result.score == 0.0
    assert result.detail["reason"] == "not submitted"


def test_hanging_solution_times_out():
    task = _kata_task("gcd")
    task.solution_code = GCD_HANGS
    task.submitted = True

    result = PytestGrader(timeout_s=2.0).grade(task, [])

    assert not result.passed
    assert result.detail.get("timeout") is True
