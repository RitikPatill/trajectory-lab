"""CRUD helpers for TrajectoryLab storage."""

from __future__ import annotations

import json
from statistics import mean

from sqlmodel import Session, select

from tlab.bench.schema import AgentConfig, BenchCase
from tlab.bench.schema import Benchmark as BenchmarkSpec
from tlab.judges.schema import JudgeVerdict
from tlab.runner.trace import Trajectory
from tlab.storage.models import (
    Agent,
    Benchmark,
    CaseResult,
    Run,
    TrajectoryRecord,
    Verdict,
)


def upsert_agent(session: Session, config: AgentConfig) -> Agent:
    """Insert or update an Agent row from an AgentConfig."""
    existing = session.exec(select(Agent).where(Agent.name == config.name)).first()
    if existing:
        existing.model = config.model
        existing.system = config.system
        existing.tools_json = json.dumps(config.tools)
        existing.max_steps = config.max_steps
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    agent = Agent(
        name=config.name,
        model=config.model,
        system=config.system,
        tools_json=json.dumps(config.tools),
        max_steps=config.max_steps,
    )
    session.add(agent)
    session.commit()
    session.refresh(agent)
    return agent


def upsert_benchmark(session: Session, bm: BenchmarkSpec) -> Benchmark:
    """Insert or update a Benchmark row from a BenchmarkSpec."""
    existing = session.exec(
        select(Benchmark).where(Benchmark.name == bm.name)
    ).first()
    if existing:
        existing.description = bm.description
        existing.case_count = len(bm.cases)
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    benchmark = Benchmark(
        name=bm.name,
        description=bm.description,
        case_count=len(bm.cases),
    )
    session.add(benchmark)
    session.commit()
    session.refresh(benchmark)
    return benchmark


def create_run(
    session: Session, agent_id: int, benchmark_id: int, total_cases: int
) -> Run:
    """Create a new Run row."""
    run = Run(agent_id=agent_id, benchmark_id=benchmark_id, total_cases=total_cases)
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def save_case_result(
    session: Session,
    run_id: int,
    case: BenchCase,
    trajectory: Trajectory,
    verdicts: list[JudgeVerdict],
) -> CaseResult:
    """Persist a CaseResult + TrajectoryRecord + Verdict rows."""
    scores = [v.score for v in verdicts]
    aggregate_score = mean(scores) if scores else 0.0
    passed = all(v.passed for v in verdicts)

    case_result = CaseResult(
        run_id=run_id,
        case_id=case.id,
        task=case.task,
        inputs_json=json.dumps(case.inputs),
        passed=passed,
        aggregate_score=aggregate_score,
    )
    session.add(case_result)
    session.commit()
    session.refresh(case_result)

    traj_record = TrajectoryRecord(
        case_result_id=case_result.id,
        data_json=trajectory.model_dump_json(),
    )
    session.add(traj_record)

    for v in verdicts:
        verdict_row = Verdict(
            case_result_id=case_result.id,
            judge=v.judge,
            passed=v.passed,
            score=v.score,
            rationale=v.rationale,
            details_json=json.dumps(v.details),
        )
        session.add(verdict_row)

    session.commit()
    return case_result


def finalize_run(session: Session, run_id: int) -> Run:
    """Compute and persist passed_cases + mean_score for a run."""
    run = session.get(Run, run_id)
    if run is None:
        raise ValueError(f"Run {run_id} not found")
    case_results = session.exec(
        select(CaseResult).where(CaseResult.run_id == run_id)
    ).all()
    run.passed_cases = sum(1 for cr in case_results if cr.passed)
    scores = [cr.aggregate_score for cr in case_results]
    run.mean_score = mean(scores) if scores else None
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def list_runs(session: Session) -> list[Run]:
    return list(session.exec(select(Run)).all())


def get_run(session: Session, run_id: int) -> Run | None:
    return session.get(Run, run_id)


def list_case_results(session: Session, run_id: int) -> list[CaseResult]:
    return list(
        session.exec(select(CaseResult).where(CaseResult.run_id == run_id)).all()
    )


def get_case_result(
    session: Session, run_id: int, case_id: str
) -> CaseResult | None:
    return session.exec(
        select(CaseResult).where(
            CaseResult.run_id == run_id, CaseResult.case_id == case_id
        )
    ).first()


def get_trajectory_record(
    session: Session, case_result_id: int
) -> TrajectoryRecord | None:
    return session.exec(
        select(TrajectoryRecord).where(
            TrajectoryRecord.case_result_id == case_result_id
        )
    ).first()


def list_verdicts(session: Session, case_result_id: int) -> list[Verdict]:
    return list(
        session.exec(
            select(Verdict).where(Verdict.case_result_id == case_result_id)
        ).all()
    )


def list_agents(session: Session) -> list[Agent]:
    return list(session.exec(select(Agent)).all())


def list_benchmarks(session: Session) -> list[Benchmark]:
    return list(session.exec(select(Benchmark)).all())
