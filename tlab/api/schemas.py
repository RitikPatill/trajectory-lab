"""Pydantic response models for TrajectoryLab API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AgentOut(BaseModel):
    id: int
    name: str
    model: str
    tools: list[str]
    max_steps: int


class BenchmarkOut(BaseModel):
    id: int
    name: str
    description: str
    case_count: int


class VerdictOut(BaseModel):
    judge: str
    passed: bool
    score: float
    rationale: str
    details: dict[str, Any]


class CaseSummary(BaseModel):
    case_id: str
    task: str
    passed: bool
    aggregate_score: float


class CaseDetail(BaseModel):
    case_id: str
    task: str
    inputs: dict[str, Any]
    passed: bool
    aggregate_score: float
    trajectory: dict[str, Any]
    verdicts: list[VerdictOut]


class RunSummary(BaseModel):
    id: int
    agent_id: int
    benchmark_id: int
    created_at: datetime
    total_cases: int
    passed_cases: int
    mean_score: float | None


class RunDetail(BaseModel):
    id: int
    agent: AgentOut
    benchmark: BenchmarkOut
    created_at: datetime
    total_cases: int
    passed_cases: int
    mean_score: float | None
    cases: list[CaseSummary]


class CaseDiff(BaseModel):
    case_id: str
    score_a: float
    score_b: float
    delta: float
    passed_a: bool
    passed_b: bool


class CompareOut(BaseModel):
    run_a: RunSummary
    run_b: RunSummary
    cases: list[CaseDiff]
