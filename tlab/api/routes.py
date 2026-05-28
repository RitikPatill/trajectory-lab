"""FastAPI application with all TrajectoryLab REST endpoints."""

from __future__ import annotations

import json
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from tlab.api.schemas import (
    AgentOut,
    BenchmarkOut,
    CaseDetail,
    CaseDiff,
    CaseSummary,
    CompareOut,
    RunDetail,
    RunSummary,
    VerdictOut,
)
from tlab.storage import (
    get_case_result,
    get_run,
    get_session,
    get_trajectory_record,
    list_agents,
    list_benchmarks,
    list_case_results,
    list_runs,
    list_verdicts,
)
from tlab.storage.models import Agent, Benchmark

app = FastAPI(
    title="TrajectoryLab",
    version="0.1.0",
    description=(
        "Evaluation harness for tool-using LLM agents. "
        "OpenAPI docs at /docs, ReDoc at /redoc."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SessionDep = Annotated[Session, Depends(get_session)]


def _agent_out(agent: Agent) -> AgentOut:
    return AgentOut(
        id=agent.id,
        name=agent.name,
        model=agent.model,
        tools=json.loads(agent.tools_json),
        max_steps=agent.max_steps,
    )


def _benchmark_out(benchmark: Benchmark) -> BenchmarkOut:
    return BenchmarkOut(
        id=benchmark.id,
        name=benchmark.name,
        description=benchmark.description,
        case_count=benchmark.case_count,
    )


@app.get("/runs", response_model=list[RunSummary])
def get_runs(session: SessionDep) -> list[RunSummary]:
    """List all runs."""
    return [
        RunSummary(
            id=r.id,
            agent_id=r.agent_id,
            benchmark_id=r.benchmark_id,
            created_at=r.created_at,
            total_cases=r.total_cases,
            passed_cases=r.passed_cases,
            mean_score=r.mean_score,
        )
        for r in list_runs(session)
    ]


@app.get("/runs/{run_id}", response_model=RunDetail)
def get_run_detail(run_id: int, session: SessionDep) -> RunDetail:
    """Get a run with all case summaries."""
    run = get_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    agent = session.get(Agent, run.agent_id)
    benchmark = session.get(Benchmark, run.benchmark_id)

    if agent is None or benchmark is None:
        raise HTTPException(
            status_code=404, detail="Associated agent or benchmark not found"
        )

    cases = [
        CaseSummary(
            case_id=cr.case_id,
            task=cr.task,
            passed=cr.passed,
            aggregate_score=cr.aggregate_score,
        )
        for cr in list_case_results(session, run_id)
    ]

    return RunDetail(
        id=run.id,
        agent=_agent_out(agent),
        benchmark=_benchmark_out(benchmark),
        created_at=run.created_at,
        total_cases=run.total_cases,
        passed_cases=run.passed_cases,
        mean_score=run.mean_score,
        cases=cases,
    )


@app.get("/runs/{run_id}/cases/{case_id}", response_model=CaseDetail)
def get_case_detail(run_id: int, case_id: str, session: SessionDep) -> CaseDetail:
    """Get a single case result with trajectory and verdicts."""
    cr = get_case_result(session, run_id, case_id)
    if cr is None:
        raise HTTPException(
            status_code=404,
            detail=f"Case '{case_id}' not found in run {run_id}",
        )

    traj_record = get_trajectory_record(session, cr.id)
    trajectory_data = json.loads(traj_record.data_json) if traj_record else {}

    verdicts = [
        VerdictOut(
            judge=v.judge,
            passed=v.passed,
            score=v.score,
            rationale=v.rationale,
            details=json.loads(v.details_json),
        )
        for v in list_verdicts(session, cr.id)
    ]

    return CaseDetail(
        case_id=cr.case_id,
        task=cr.task,
        inputs=json.loads(cr.inputs_json),
        passed=cr.passed,
        aggregate_score=cr.aggregate_score,
        trajectory=trajectory_data,
        verdicts=verdicts,
    )


@app.get("/agents", response_model=list[AgentOut])
def get_agents(session: SessionDep) -> list[AgentOut]:
    """List all registered agents."""
    return [_agent_out(a) for a in list_agents(session)]


@app.get("/benchmarks", response_model=list[BenchmarkOut])
def get_benchmarks(session: SessionDep) -> list[BenchmarkOut]:
    """List all registered benchmarks."""
    return [_benchmark_out(b) for b in list_benchmarks(session)]


@app.get("/compare", response_model=CompareOut)
def compare_runs(
    session: SessionDep,
    a: int = Query(..., description="First run ID"),
    b: int = Query(..., description="Second run ID"),
) -> CompareOut:
    """Compare two runs side-by-side on shared cases."""
    run_a = get_run(session, a)
    run_b = get_run(session, b)

    if run_a is None:
        raise HTTPException(status_code=404, detail=f"Run {a} not found")
    if run_b is None:
        raise HTTPException(status_code=404, detail=f"Run {b} not found")

    cases_a = {cr.case_id: cr for cr in list_case_results(session, a)}
    cases_b = {cr.case_id: cr for cr in list_case_results(session, b)}

    shared_ids = sorted(set(cases_a.keys()) & set(cases_b.keys()))

    diffs = [
        CaseDiff(
            case_id=cid,
            score_a=cases_a[cid].aggregate_score,
            score_b=cases_b[cid].aggregate_score,
            delta=cases_b[cid].aggregate_score - cases_a[cid].aggregate_score,
            passed_a=cases_a[cid].passed,
            passed_b=cases_b[cid].passed,
        )
        for cid in shared_ids
    ]

    def to_summary(run):
        return RunSummary(
            id=run.id,
            agent_id=run.agent_id,
            benchmark_id=run.benchmark_id,
            created_at=run.created_at,
            total_cases=run.total_cases,
            passed_cases=run.passed_cases,
            mean_score=run.mean_score,
        )

    return CompareOut(run_a=to_summary(run_a), run_b=to_summary(run_b), cases=diffs)
