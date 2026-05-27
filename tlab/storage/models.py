"""SQLModel table definitions for TrajectoryLab storage."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class Agent(SQLModel, table=True):
    __tablename__ = "agent"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    model: str
    system: str
    tools_json: str = Field(default="[]")
    max_steps: int = 10


class Benchmark(SQLModel, table=True):
    __tablename__ = "benchmark"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str = ""
    case_count: int = 0


class Run(SQLModel, table=True):
    __tablename__ = "run"

    id: int | None = Field(default=None, primary_key=True)
    agent_id: int = Field(foreign_key="agent.id")
    benchmark_id: int = Field(foreign_key="benchmark.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    total_cases: int = 0
    passed_cases: int = 0
    mean_score: float | None = None


class CaseResult(SQLModel, table=True):
    __tablename__ = "case_result"

    id: int | None = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="run.id")
    case_id: str
    task: str
    inputs_json: str = Field(default="{}")
    passed: bool = False
    aggregate_score: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TrajectoryRecord(SQLModel, table=True):
    __tablename__ = "trajectory"

    id: int | None = Field(default=None, primary_key=True)
    case_result_id: int = Field(foreign_key="case_result.id")
    data_json: str = Field(default="{}")


class Verdict(SQLModel, table=True):
    __tablename__ = "verdict"

    id: int | None = Field(default=None, primary_key=True)
    case_result_id: int = Field(foreign_key="case_result.id")
    judge: str
    passed: bool = False
    score: float = 0.0
    rationale: str = ""
    details_json: str = Field(default="{}")
