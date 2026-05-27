"""Tests for tlab.judges — no live API calls."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from tlab.bench.schema import BenchCase, OutputValidator, Rubric, RubricCriterion
from tlab.judges import OutputJudge, RubricJudge, TrajectoryJudge
from tlab.runner.trace import Step, ToolCall, ToolResult, Trajectory

# ---------------------------------------------------------------------------
# Helpers — trajectory builders
# ---------------------------------------------------------------------------


def _trajectory(
    final_response: str | None = "some response",
    steps: list[Step] | None = None,
) -> Trajectory:
    return Trajectory(
        run_id="test-run",
        model="claude-haiku-4-5-20251001",
        system="test",
        initial_messages=[{"role": "user", "content": "test"}],
        steps=steps or [],
        final_response=final_response,
    )


def _step_with_tool_call(name: str, step_index: int = 0) -> Step:
    return Step(
        index=step_index,
        role="assistant",
        raw_content=[],
        tool_calls=[ToolCall(tool_use_id=f"tu_{step_index}", name=name, input={})],
    )


def _step_with_tool_results(
    results: list[tuple[str, bool]], step_index: int = 1
) -> Step:
    return Step(
        index=step_index,
        role="tool",
        raw_content=[],
        tool_results=[
            ToolResult(
                tool_use_id=f"tu_{i}",
                name=name,
                content="result",
                is_error=is_error,
            )
            for i, (name, is_error) in enumerate(results)
        ],
    )


def _case(
    expected_tools: list[str] | None = None,
    output_validators: list[OutputValidator] | None = None,
    rubric: Rubric | None = None,
    max_steps: int | None = None,
) -> BenchCase:
    return BenchCase(
        id="test-case",
        task="Test task",
        inputs={},
        expected_tools=expected_tools or [],
        max_steps=max_steps,
        output_validators=output_validators or [],
        rubric=rubric,
    )


# ---------------------------------------------------------------------------
# Mock client for RubricJudge
# ---------------------------------------------------------------------------


def _mock_rubric_client(grades: list[dict]) -> MagicMock:
    """Return mock Anthropic client whose messages.create() returns grade_rubric."""
    tool_use_block = SimpleNamespace(
        type="tool_use",
        input={"grades": grades},
    )
    api_response = MagicMock()
    api_response.content = [tool_use_block]

    client = MagicMock()
    client.messages.create.return_value = api_response
    return client


# ---------------------------------------------------------------------------
# OutputJudge tests (8 tests)
# ---------------------------------------------------------------------------


def test_output_no_validators_passes():
    judge = OutputJudge()
    verdict = judge.judge(_trajectory(), _case())
    assert verdict.passed is True
    assert verdict.score == 1.0


def test_output_none_response_fails():
    judge = OutputJudge()
    case = _case(output_validators=[OutputValidator(type="exact_match", value="hello")])
    verdict = judge.judge(_trajectory(final_response=None), case)
    assert verdict.passed is False
    assert verdict.score == 0.0


def test_output_exact_match_pass():
    judge = OutputJudge()
    case = _case(
        output_validators=[OutputValidator(type="exact_match", value="Paris is the capital")]
    )
    verdict = judge.judge(_trajectory(final_response="Paris is the capital"), case)
    assert verdict.passed is True
    assert verdict.score == 1.0


def test_output_exact_match_fail():
    judge = OutputJudge()
    case = _case(output_validators=[OutputValidator(type="exact_match", value="Berlin")])
    verdict = judge.judge(_trajectory(final_response="Paris is the capital"), case)
    assert verdict.passed is False
    assert verdict.score == 0.0


def test_output_regex_pass():
    judge = OutputJudge()
    case = _case(output_validators=[OutputValidator(type="regex", value=r"\d+")])
    verdict = judge.judge(_trajectory(final_response="The answer is 42"), case)
    assert verdict.passed is True


def test_output_regex_fail():
    judge = OutputJudge()
    case = _case(output_validators=[OutputValidator(type="regex", value=r"^\d+$")])
    verdict = judge.judge(_trajectory(final_response="not a number"), case)
    assert verdict.passed is False


def test_output_json_schema_pass():
    judge = OutputJudge()
    schema = json.dumps(
        {
            "type": "object",
            "properties": {"answer": {"type": "number"}},
            "required": ["answer"],
        }
    )
    case = _case(output_validators=[OutputValidator(type="json_schema", value=schema)])
    response = json.dumps({"answer": 42})
    verdict = judge.judge(_trajectory(final_response=response), case)
    assert verdict.passed is True


def test_output_json_schema_fail():
    judge = OutputJudge()
    schema = json.dumps(
        {
            "type": "object",
            "properties": {"answer": {"type": "number"}},
            "required": ["answer"],
        }
    )
    case = _case(output_validators=[OutputValidator(type="json_schema", value=schema)])
    response = json.dumps({"answer": "not a number"})
    verdict = judge.judge(_trajectory(final_response=response), case)
    assert verdict.passed is False


# ---------------------------------------------------------------------------
# TrajectoryJudge tests (5 tests)
# ---------------------------------------------------------------------------


def test_trajectory_expected_tool_present():
    judge = TrajectoryJudge()
    steps = [
        _step_with_tool_call("web_search", 0),
        _step_with_tool_results([("web_search", False)], 1),
    ]
    verdict = judge.judge(
        _trajectory(steps=steps), _case(expected_tools=["web_search"])
    )
    assert verdict.passed is True
    assert verdict.details["missing_tools"] == []


def test_trajectory_expected_tool_missing():
    judge = TrajectoryJudge()
    steps = [
        _step_with_tool_call("calculator", 0),
    ]
    verdict = judge.judge(
        _trajectory(steps=steps), _case(expected_tools=["web_search"])
    )
    assert verdict.passed is False
    assert "web_search" in verdict.details["missing_tools"]


def test_trajectory_no_expected_tools():
    judge = TrajectoryJudge()
    verdict = judge.judge(_trajectory(), _case(expected_tools=[]))
    assert verdict.passed is True
    assert verdict.details["expected_tools_called"] is True


def test_trajectory_no_error_loop():
    judge = TrajectoryJudge()
    # Two scattered errors but no window of 3 consecutive errors
    steps = [
        _step_with_tool_results(
            [("web_search", True), ("calculator", False), ("web_search", True)], 0
        ),
    ]
    verdict = judge.judge(_trajectory(steps=steps), _case())
    assert verdict.passed is True
    assert verdict.details["error_loop_detected"] is False


def test_trajectory_error_loop_detected():
    judge = TrajectoryJudge()
    # 3 consecutive tool results all is_error=True
    steps = [
        _step_with_tool_results(
            [("web_search", True), ("web_search", True), ("web_search", True)], 0
        ),
    ]
    verdict = judge.judge(_trajectory(steps=steps), _case())
    assert verdict.passed is False
    assert verdict.details["error_loop_detected"] is True


def test_trajectory_max_steps_not_exceeded():
    judge = TrajectoryJudge()
    steps = [_step_with_tool_call("web_search", i) for i in range(3)]
    verdict = judge.judge(_trajectory(steps=steps), _case(max_steps=5))
    assert verdict.passed is True
    assert verdict.details["max_steps_ok"] is True


def test_trajectory_max_steps_exceeded():
    judge = TrajectoryJudge()
    steps = [_step_with_tool_call("web_search", i) for i in range(6)]
    verdict = judge.judge(_trajectory(steps=steps), _case(max_steps=5))
    assert verdict.passed is False
    assert verdict.details["max_steps_ok"] is False


def test_trajectory_max_steps_not_set():
    judge = TrajectoryJudge()
    steps = [_step_with_tool_call("web_search", i) for i in range(100)]
    verdict = judge.judge(_trajectory(steps=steps), _case(max_steps=None))
    # max_steps not configured — check is skipped, should not fail on step count
    assert verdict.details["max_steps_ok"] is None


# ---------------------------------------------------------------------------
# RubricJudge tests (4 tests — all with mock client)
# ---------------------------------------------------------------------------


def test_rubric_no_rubric_passes():
    judge = RubricJudge(client=_mock_rubric_client([]))
    verdict = judge.judge(_trajectory(), _case(rubric=None))
    assert verdict.passed is True
    assert verdict.score == 1.0


def test_rubric_high_score_passes():
    rubric = Rubric(
        criteria=[
            RubricCriterion(id="accuracy", description="Is it accurate?", weight=1.0)
        ],
        pass_threshold=0.7,
    )
    client = _mock_rubric_client(
        [{"criterion_id": "accuracy", "score": 0.9, "rationale": "Good"}]
    )
    judge = RubricJudge(client=client)
    verdict = judge.judge(_trajectory(), _case(rubric=rubric))
    assert verdict.passed is True
    assert abs(verdict.score - 0.9) < 1e-6


def test_rubric_low_score_fails():
    rubric = Rubric(
        criteria=[
            RubricCriterion(id="accuracy", description="Is it accurate?", weight=1.0)
        ],
        pass_threshold=0.7,
    )
    client = _mock_rubric_client(
        [{"criterion_id": "accuracy", "score": 0.4, "rationale": "Poor"}]
    )
    judge = RubricJudge(client=client)
    verdict = judge.judge(_trajectory(), _case(rubric=rubric))
    assert verdict.passed is False
    assert abs(verdict.score - 0.4) < 1e-6


def test_rubric_weighted_average():
    rubric = Rubric(
        criteria=[
            RubricCriterion(id="accuracy", description="Accurate?", weight=2.0),
            RubricCriterion(id="clarity", description="Clear?", weight=1.0),
        ],
        pass_threshold=0.7,
    )
    # accuracy=1.0*2 + clarity=0.0*1 / 3 = 0.666...
    client = _mock_rubric_client(
        [
            {"criterion_id": "accuracy", "score": 1.0, "rationale": "Perfect"},
            {"criterion_id": "clarity", "score": 0.0, "rationale": "Terrible"},
        ]
    )
    judge = RubricJudge(client=client)
    verdict = judge.judge(_trajectory(), _case(rubric=rubric))
    expected_score = (1.0 * 2.0 + 0.0 * 1.0) / 3.0
    assert abs(verdict.score - expected_score) < 1e-6
    assert verdict.passed is False  # 0.666 < 0.7
