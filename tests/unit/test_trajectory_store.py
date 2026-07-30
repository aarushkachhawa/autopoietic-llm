from autopoietic.core.grader import GradeResult
from autopoietic.core.trajectory import Message, Trajectory
from autopoietic.core.types import Outcome
from autopoietic.storage.trajectory_store import TrajectoryStore


def _traj(traj_id: str, task_id: str, outcome: Outcome) -> Trajectory:
    return Trajectory(
        trajectory_id=traj_id,
        task_id=task_id,
        task_domain="coding_katas",
        messages=[Message(role="user", content="hi")],
        outcome=outcome,
        grade=GradeResult(
            passed=outcome == Outcome.SUCCESS,
            score=1.0 if outcome == Outcome.SUCCESS else 0.0,
        ),
    )


def test_append_and_query_all(tmp_path):
    store = TrajectoryStore(tmp_path / "trajectories")
    store.append(_traj("a", "fizzbuzz", Outcome.SUCCESS))
    store.append(_traj("b", "gcd", Outcome.FAILURE))
    store.append(_traj("c", "fizzbuzz", Outcome.FAILURE))

    assert len(store.query()) == 3


def test_query_filters_by_outcome(tmp_path):
    store = TrajectoryStore(tmp_path / "trajectories")
    store.append(_traj("a", "fizzbuzz", Outcome.SUCCESS))
    store.append(_traj("b", "gcd", Outcome.FAILURE))

    successes = store.query(outcome=Outcome.SUCCESS)
    assert len(successes) == 1
    assert successes[0].task_id == "fizzbuzz"


def test_query_filters_by_unknown_domain_returns_empty(tmp_path):
    store = TrajectoryStore(tmp_path / "trajectories")
    store.append(_traj("a", "fizzbuzz", Outcome.SUCCESS))

    assert store.query(domain="nonexistent") == []


def test_reopening_store_continues_line_numbering(tmp_path):
    root = tmp_path / "trajectories"
    store1 = TrajectoryStore(root)
    store1.append(_traj("a", "fizzbuzz", Outcome.SUCCESS))

    store2 = TrajectoryStore(root)
    store2.append(_traj("b", "gcd", Outcome.FAILURE))

    assert len(store2.query()) == 2
