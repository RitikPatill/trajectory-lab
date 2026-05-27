"""TrajectoryJudge — deterministic checks on the agent trace."""

from __future__ import annotations

from tlab.bench.schema import BenchCase
from tlab.judges.schema import JudgeVerdict
from tlab.runner.trace import Trajectory


class TrajectoryJudge:
    """Runs deterministic structural checks on a Trajectory.

    Contract: accepts a Trajectory and BenchCase, returns a JudgeVerdict.
    No API calls are made.
    """

    name: str = "trajectory"

    def judge(self, trajectory: Trajectory, case: BenchCase) -> JudgeVerdict:
        checks: dict[str, bool] = {}
        missing_tools: list[str] = []

        # Check 1: expected tools were called
        called_tool_names = {
            tc.name
            for step in trajectory.steps
            for tc in step.tool_calls
        }
        if case.expected_tools:
            missing_tools = [
                t for t in case.expected_tools if t not in called_tool_names
            ]
            checks["expected_tools_called"] = len(missing_tools) == 0
        else:
            checks["expected_tools_called"] = True

        # Check 2: step count does not exceed max_steps
        if case.max_steps is not None:
            checks["max_steps"] = len(trajectory.steps) <= case.max_steps

        # Check 3: no error loop (3 consecutive tool results all is_error=True)
        all_results = [
            tr
            for step in trajectory.steps
            for tr in step.tool_results
        ]
        error_loop = False
        for i in range(len(all_results) - 2):
            window = all_results[i], all_results[i + 1], all_results[i + 2]
            if all(r.is_error for r in window):
                error_loop = True
                break
        checks["no_error_loop"] = not error_loop

        total = len(checks)
        passed_count = sum(1 for v in checks.values() if v)
        score = passed_count / total
        passed = score == 1.0

        rationale_parts = []
        if not checks["expected_tools_called"]:
            rationale_parts.append(f"missing tools: {missing_tools}")
        if "max_steps" in checks and not checks["max_steps"]:
            rationale_parts.append(
                f"exceeded max_steps ({len(trajectory.steps)} > {case.max_steps})"
            )
        if not checks["no_error_loop"]:
            rationale_parts.append("error loop detected")
        rationale = (
            "; ".join(rationale_parts) if rationale_parts else "all checks passed"
        )

        return JudgeVerdict(
            judge=self.name,
            passed=passed,
            score=score,
            rationale=rationale,
            details={
                "expected_tools_called": checks["expected_tools_called"],
                "missing_tools": missing_tools,
                "max_steps_ok": checks.get("max_steps"),
                "error_loop_detected": error_loop,
                "total_steps": len(trajectory.steps),
            },
        )
