"""OutputJudge — deterministic regex / json-schema / exact-match validator."""

from __future__ import annotations

import json
import re
from typing import Any

import jsonschema

from tlab.bench.schema import BenchCase
from tlab.judges.schema import JudgeVerdict
from tlab.runner.trace import Trajectory


class OutputJudge:
    """Validates the trajectory's final_response against OutputValidator rules.

    Contract: accepts a Trajectory and BenchCase, returns a JudgeVerdict.
    No API calls are made; all checks are deterministic.
    """

    name: str = "output"

    def judge(self, trajectory: Trajectory, case: BenchCase) -> JudgeVerdict:
        if not case.output_validators:
            return JudgeVerdict(
                judge=self.name,
                passed=True,
                score=1.0,
                rationale="No validators defined",
                details={"results": []},
            )

        if trajectory.final_response is None:
            results: list[dict[str, Any]] = [
                {"type": v.type, "value": v.value, "passed": False}
                for v in case.output_validators
            ]
            return JudgeVerdict(
                judge=self.name,
                passed=False,
                score=0.0,
                rationale="No final response to validate",
                details={"results": results},
            )

        response = trajectory.final_response
        results = []
        for validator in case.output_validators:
            ok = self._check(validator.type, validator.value, response)
            results.append(
                {"type": validator.type, "value": validator.value, "passed": ok}
            )

        passed_count = sum(1 for r in results if r["passed"])
        total = len(results)
        score = passed_count / total
        passed = score == 1.0
        rationale = f"{passed_count}/{total} validators passed"

        return JudgeVerdict(
            judge=self.name,
            passed=passed,
            score=score,
            rationale=rationale,
            details={"results": results},
        )

    def _check(self, vtype: str, value: str, response: str) -> bool:
        if vtype == "exact_match":
            return response == value
        if vtype == "regex":
            return bool(re.search(value, response))
        if vtype == "json_schema":
            try:
                parsed = json.loads(response)
                schema = json.loads(value)
                jsonschema.validate(parsed, schema)
                return True
            except (json.JSONDecodeError, jsonschema.ValidationError):
                return False
        return False
