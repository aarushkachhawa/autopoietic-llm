from autopoietic.tasks.coding_katas.task import CodingKataTask, load_katas
from autopoietic.tasks.registry import KATAS_DIR


def _kata_task(kata_id: str) -> CodingKataTask:
    spec = next(s for s in load_katas(KATAS_DIR) if s.id == kata_id)
    return CodingKataTask(spec)


def test_load_katas_finds_seed_set():
    specs = load_katas(KATAS_DIR)
    ids = {s.id for s in specs}
    assert {"fizzbuzz", "reverse_string", "is_palindrome", "two_sum", "gcd"} <= ids
    for spec in specs:
        assert spec.test_file.exists()
        assert spec.prompt.strip()


def test_write_file_then_submit_marks_terminal():
    task = _kata_task("fizzbuzz")
    assert not task.is_terminal([])

    result = task.handle_tool_call("write_file", {"content": "def fizzbuzz(n): return []"})
    assert result.success
    assert not task.is_terminal([])

    result = task.handle_tool_call("submit", {})
    assert result.success
    assert task.is_terminal([])


def test_write_file_rejects_empty_content():
    task = _kata_task("gcd")
    result = task.handle_tool_call("write_file", {"content": ""})
    assert not result.success


def test_run_tests_reports_syntax_error():
    task = _kata_task("gcd")
    task.handle_tool_call("write_file", {"content": "def gcd(a, b:\n    pass"})
    result = task.handle_tool_call("run_tests", {})
    assert not result.success
    assert "SyntaxError" in result.output


def test_run_tests_reports_clean_compile():
    task = _kata_task("gcd")
    task.handle_tool_call("write_file", {"content": "def gcd(a, b):\n    return a\n"})
    result = task.handle_tool_call("run_tests", {})
    assert result.success


def test_unknown_tool_name_is_rejected_by_task():
    task = _kata_task("gcd")
    result = task.handle_tool_call("delete_everything", {})
    assert not result.success
