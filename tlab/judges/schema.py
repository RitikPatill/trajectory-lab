"""Shared Pydantic models for judge verdicts."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CriterionGrade(BaseModel):
    criterion_id: str
    score: float  # 0.0–1.0
    rationale: str


class JudgeVerdict(BaseModel):
    judge: str  # "output" | "trajectory" | "rubric"
    passed: bool
    score: float  # 0.0–1.0 weighted aggregate
    rationale: str
    details: dict[str, Any] = Field(default_factory=dict)
