"""RubricJudge — LLM-as-judge using Anthropic forced tool use."""

from __future__ import annotations

import anthropic

from tlab.bench.schema import BenchCase, Rubric
from tlab.judges.schema import CriterionGrade, JudgeVerdict
from tlab.runner.trace import Trajectory

_GRADE_TOOL: dict = {
    "name": "grade_rubric",
    "description": "Return grades for every rubric criterion.",
    "input_schema": {
        "type": "object",
        "properties": {
            "grades": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "criterion_id": {"type": "string"},
                        "score": {"type": "number", "minimum": 0, "maximum": 1},
                        "rationale": {"type": "string"},
                    },
                    "required": ["criterion_id", "score", "rationale"],
                },
            }
        },
        "required": ["grades"],
    },
}


class RubricJudge:
    """LLM-as-judge that grades a trajectory against a YAML rubric.

    Contract: accepts a Trajectory and BenchCase, returns a JudgeVerdict.
    Uses Claude via forced tool use so criterion grades are structured JSON.
    Client is injectable for testing (no live API key required in tests).
    """

    def __init__(
        self,
        model: str = "claude-haiku-4-5-20251001",
        client: anthropic.Anthropic | None = None,
    ) -> None:
        self.model = model
        self._client = client or anthropic.Anthropic()

    def judge(self, trajectory: Trajectory, case: BenchCase) -> JudgeVerdict:
        if case.rubric is None:
            return JudgeVerdict(
                judge="rubric",
                passed=True,
                score=1.0,
                rationale="No rubric defined",
                details={},
            )

        summary = _build_trajectory_summary(trajectory)
        response_text = trajectory.final_response or ""
        grades = self._grade(case.rubric, case.task, response_text, summary)

        total_weight = sum(c.weight for c in case.rubric.criteria)
        if total_weight == 0:
            weighted_score = 0.0
        else:
            weighted_score = sum(
                g.score
                * next(
                    (c.weight for c in case.rubric.criteria if c.id == g.criterion_id),
                    1.0,
                )
                for g in grades
            ) / total_weight

        passed = weighted_score >= case.rubric.pass_threshold
        rationale = (
            f"weighted score {weighted_score:.2f} "
            f"({'pass' if passed else 'fail'}, threshold {case.rubric.pass_threshold})"
        )

        return JudgeVerdict(
            judge="rubric",
            passed=passed,
            score=weighted_score,
            rationale=rationale,
            details={
                "grades": [
                    {
                        "criterion_id": g.criterion_id,
                        "score": g.score,
                        "rationale": g.rationale,
                    }
                    for g in grades
                ],
                "pass_threshold": case.rubric.pass_threshold,
            },
        )

    def _grade(
        self,
        rubric: Rubric,
        task: str,
        response: str,
        trajectory_summary: str,
    ) -> list[CriterionGrade]:
        criteria_text = "\n".join(
            f"- {c.id} (weight {c.weight}): {c.description}"
            for c in rubric.criteria
        )
        user_prompt = (
            f"Task: {task}\n\n"
            f"Trajectory summary:\n{trajectory_summary}\n\n"
            f"Final response:\n{response}\n\n"
            f"Rubric criteria:\n{criteria_text}\n\n"
            "Grade each criterion using the grade_rubric tool."
        )

        api_response = self._client.messages.create(
            model=self.model,
            max_tokens=1024,
            system="You are a strict, impartial judge.",
            messages=[{"role": "user", "content": user_prompt}],
            tools=[_GRADE_TOOL],
            tool_choice={"type": "tool", "name": "grade_rubric"},
        )

        raw_grades = api_response.content[0].input["grades"]
        return [CriterionGrade(**g) for g in raw_grades]


def _build_trajectory_summary(trajectory: Trajectory) -> str:
    """Build a compact human-readable summary of the trajectory steps."""
    lines: list[str] = []
    step_num = 0
    for step in trajectory.steps:
        step_num += 1
        if step.role == "assistant":
            if step.tool_calls:
                for tc in step.tool_calls:
                    lines.append(
                        f"Step {step_num} [assistant]: called {tc.name}({tc.input})"
                    )
            else:
                lines.append(f"Step {step_num} [assistant]: final response")
        elif step.role == "tool":
            for tr in step.tool_results:
                status = "error" if tr.is_error else "ok"
                preview = tr.content[:100]
                lines.append(
                    f"Step {step_num} [tool]: {tr.name} → {preview} [{status}]"
                )

    summary = "\n".join(lines)
    if len(summary) > 2000:
        summary = summary[:1997] + "..."
    return summary
