"""Tests for SQLite storage layer — no live API calls required."""

from __future__ import annotations

from statistics import mean

import pytest
from sqlmodel import Session, select

from tlab.bench.schema import AgentConfig, BenchCase
from tlab.bench.schema import Benchmark as BenchmarkSpec
from tlab.judges.schema import JudgeVerdict
from tlab.runner.trace import Trajectory
from tlab.storage import (
    create_run,
    finalize_run,
    get_engine,
    get_run,
    list_case_results,
    list_runs,
    reset_engine,
    save_case_result,
    upsert_agent,
    upsert_benchmark,
)
from tlab.storage.models import TrajectoryRecord, Verdict


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch, tmp_path):
    """Give every test its own fresh SQLite DB."""
    reset_engine()
    db = tmp_path / "test.db"
    monkeypatch.setenv("TLAB_DB", str(db))
    yield
    reset_engine()


# ── helpers ────────────────────────────────────────────────────────────────


def _agent_config(name: str = "test-agent") -> AgentConfig:
    return AgentConfig(
        name=name,
        model="claude-haiku-4-5-20251001",
        system="You are a test agent.",
        tools=["web_search"],
        max_steps=5,
    )


def _benchmark_spec(name: str = "test-bench", n_cases: int = 2) -> BenchmarkSpec:
    cases = [
        BenchCase(id=f"case_{i:03d}", task=f"Task {i}", inputs={"q": f"q{i}"})
        for i in range(n_cases)
    ]
    return BenchmarkSpec(name=name, description="A test benchmark", cases=cases)


def _trajectory() -> Trajectory:
    return Trajectory(
        run_id="traj-001",
        model="claude-haiku-4-5-20251001",
        system="sys",
        initial_messages=[{"role": "user", "content": "hello"}],
        final_response="done",
    )


def _verdicts(
    scores: tuple = (0.8, 0.9, 1.0), passed: tuple = (True, True, True)
) -> list[JudgeVerdict]:
    names = ["output", "trajectory", "rubric"]
    return [
        JudgeVerdict(judge=n, passed=p, score=s, rationale="ok", details={})
        for n, s, p in zip(names, scores, passed)
    ]


# ── tests ──────────────────────────────────────────────────────────────────


def test_upsert_agent_creates():
    with Session(get_engine()) as session:
        agent = upsert_agent(session, _agent_config())
        assert agent.id is not None
        assert agent.name == "test-agent"


def test_upsert_agent_is_idempotent():
    with Session(get_engine()) as session:
        a1 = upsert_agent(session, _agent_config())
        a1_id = a1.id
        a2 = upsert_agent(session, _agent_config())
        assert a1_id == a2.id


def test_upsert_benchmark_creates():
    spec = _benchmark_spec(n_cases=3)
    with Session(get_engine()) as session:
        bm = upsert_benchmark(session, spec)
        assert bm.id is not None
        assert bm.case_count == 3


def test_create_run():
    with Session(get_engine()) as session:
        agent = upsert_agent(session, _agent_config())
        bm = upsert_benchmark(session, _benchmark_spec())
        agent_id = agent.id
        bm_id = bm.id
        run = create_run(session, agent_id, bm_id, total_cases=5)
        assert run.agent_id == agent_id
        assert run.benchmark_id == bm_id
        assert run.total_cases == 5


def test_save_case_result_rows():
    spec = _benchmark_spec()
    case = spec.cases[0]
    with Session(get_engine()) as session:
        agent = upsert_agent(session, _agent_config())
        bm = upsert_benchmark(session, spec)
        run = create_run(session, agent.id, bm.id, total_cases=2)
        cr = save_case_result(session, run.id, case, _trajectory(), _verdicts())

        traj_rows = session.exec(
            select(TrajectoryRecord).where(TrajectoryRecord.case_result_id == cr.id)
        ).all()
        verdict_rows = session.exec(
            select(Verdict).where(Verdict.case_result_id == cr.id)
        ).all()

        assert len(traj_rows) == 1
        assert len(verdict_rows) == 3


def test_aggregate_score():
    scores = (0.8, 0.6, 1.0)
    spec = _benchmark_spec()
    case = spec.cases[0]
    with Session(get_engine()) as session:
        agent = upsert_agent(session, _agent_config())
        bm = upsert_benchmark(session, spec)
        run = create_run(session, agent.id, bm.id, total_cases=2)
        cr = save_case_result(
            session, run.id, case, _trajectory(), _verdicts(scores=scores)
        )
        agg = cr.aggregate_score

    assert abs(agg - mean(scores)) < 1e-9


def test_finalize_run_stats():
    spec = _benchmark_spec(n_cases=2)
    case_pass = spec.cases[0]
    case_fail = spec.cases[1]
    with Session(get_engine()) as session:
        agent = upsert_agent(session, _agent_config())
        bm = upsert_benchmark(session, spec)
        run = create_run(session, agent.id, bm.id, total_cases=2)
        save_case_result(
            session,
            run.id,
            case_pass,
            _trajectory(),
            _verdicts(scores=(1.0, 1.0, 1.0), passed=(True, True, True)),
        )
        save_case_result(
            session,
            run.id,
            case_fail,
            _trajectory(),
            _verdicts(scores=(0.0, 0.0, 0.0), passed=(False, False, False)),
        )
        finalized = finalize_run(session, run.id)
        assert finalized.passed_cases == 1
        expected_mean = mean([1.0, 0.0])
        assert abs(finalized.mean_score - expected_mean) < 1e-9


def test_list_runs():
    with Session(get_engine()) as session:
        agent = upsert_agent(session, _agent_config())
        bm = upsert_benchmark(session, _benchmark_spec())
        create_run(session, agent.id, bm.id, total_cases=1)
        runs = list_runs(session)
    assert len(runs) == 1


def test_get_run_not_found():
    with Session(get_engine()) as session:
        result = get_run(session, 9999)
    assert result is None


def test_list_case_results():
    spec = _benchmark_spec(n_cases=2)
    with Session(get_engine()) as session:
        agent = upsert_agent(session, _agent_config())
        bm = upsert_benchmark(session, spec)
        run = create_run(session, agent.id, bm.id, total_cases=2)
        for case in spec.cases:
            save_case_result(session, run.id, case, _trajectory(), _verdicts())
        results = list_case_results(session, run.id)
    assert len(results) == 2
