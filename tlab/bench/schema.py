"""Pydantic v2 models for benchmark schema."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class OutputValidator(BaseModel):
    type: Literal["exact_match", "regex", "json_schema"]
    value: str


class RubricCriterion(BaseModel):
    id: str
    description: str
    weight: float = 1.0


class Rubric(BaseModel):
    criteria: list[RubricCriterion]
    pass_threshold: float = 0.7


class BenchCase(BaseModel):
    id: str
    task: str
    inputs: dict[str, Any]
    expected_tools: list[str] = Field(default_factory=list)
    max_steps: int | None = None
    rubric: Rubric | None = None
    output_validators: list[OutputValidator] = Field(default_factory=list)


class Benchmark(BaseModel):
    name: str
    description: str = ""
    cases: list[BenchCase]


class AgentConfig(BaseModel):
    name: str
    model: str = "claude-haiku-4-5-20251001"
    system: str
    tools: list[str] = Field(default_factory=list)
    max_steps: int = 10
