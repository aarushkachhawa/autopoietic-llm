from autopoietic.core.grader import GradeResult
from autopoietic.core.trajectory import Message, Trajectory
from autopoietic.core.types import Outcome


def test_round_trip_through_json():
    traj = Trajectory(
        trajectory_id="t1",
        task_id="fizzbuzz",
        task_domain="coding_katas",
        messages=[Message(role="user", content="hi"), Message(role="assistant", content="ok")],
        outcome=Outcome.SUCCESS,
        grade=GradeResult(passed=True, score=1.0, detail={"tests_passed": 3}),
        metadata={"num_turns": 2},
    )
    restored = Trajectory.model_validate_json(traj.model_dump_json())
    assert restored == traj


def test_adapter_version_defaults_to_none():
    traj = Trajectory(
        trajectory_id="t2",
        task_id="gcd",
        task_domain="coding_katas",
        messages=[],
        outcome=Outcome.FAILURE,
        grade=GradeResult(passed=False, score=0.0),
    )
    assert traj.adapter_version is None
