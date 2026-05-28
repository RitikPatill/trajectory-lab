"""Tests for FastAPI routes — no live API calls required."""

from __future__ import annotations

import pytest
from sqlmodel import Session
from starlette.testclient import TestClient

from tlab.api.routes import app
from tlab.bench.schema import AgentConfig, BenchCase
from tlab.bench.schema import Benchmark as BenchmarkSpec
from tlab.judges.schema import JudgeVerdict
from tlab.runner.trace import Trajectory
from tlab.storage import (
    create_run,
    finalize_run,
    get_engine,
    get_session,
    reset_engine,
    save_case_result,
    upsert_agent,
    upsert_benchmark,
)


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch, tmp_path):
    """Fresh DB for every test; override FastAPI session dependency."""
    reset_engine()
    db = tmp_path / "api_test.db"
    monkeypatch.setenv("TLAB_DB", str(db))
    # Override the FastAPI dependency to use the same engine
    app.dependency_overrides[get_session] = _session_override
    yield
    app.dependency_overrides.clear()
    reset_engine()


def _session_override():
    with Session(get_engine()) as session:
        yield session


# ── seed helpers ────────────────────────────────────────────────────────────

def _seed_one_run(n_cases: int = 2) -> int:
    """Seed Agent + Benchmark + Run + n CaseResults; return run id."""
    cfg = AgentConfig(
        name="api-test-agent",
        model="claude-haiku-4-5-20251001",
        system="sys",
        tools=["web_search"],
        max_steps=5,
    )
    spec = BenchmarkSpec(
        name="api-test-bench",
        description="desc",
        cases=[
            BenchCase(
                id=f"case_{i:03d}",
                task=f"Task {i}",
                inputs={"user_message": f"msg {i}"},
            )
            for i in range(n_cases)
        ],
    )
    traj = Trajectory(
        run_id="x",
        model="claude-haiku-4-5-20251001",
        system="sys",
        initial_messages=[{"role": "user", "content": "hi"}],
        final_response="done",
    )
    verdicts = [
        JudgeVerdict(
            judge="output", passed=True, score=1.0, rationale="ok", details={}
        ),
        JudgeVerdict(
            judge="trajectory", passed=True, score=1.0, rationale="ok", details={}
        ),
        JudgeVerdict(
            judge="rubric", passed=True, score=1.0, rationale="ok", details={}
        ),
    ]
    with Session(get_engine()) as session:
        agent_rec = upsert_agent(session, cfg)
        bm_rec = upsert_benchmark(session, spec)
        run_rec = create_run(session, agent_rec.id, bm_rec.id, total_cases=n_cases)
        for case in spec.cases:
            save_case_result(session, run_rec.id, case, traj, verdicts)
        finalize_run(session, run_rec.id)
        return run_rec.id


# ── tests ────────────────────────────────────────────────────────────────────

def test_list_runs_ok():
    _seed_one_run()
    client = TestClient(app)
    resp = client.get("/runs")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1


def test_get_run_detail():
    run_id = _seed_one_run()
    client = TestClient(app)
    resp = client.get(f"/runs/{run_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert "cases" in body
    assert len(body["cases"]) == 2


def test_get_case_detail():
    run_id = _seed_one_run()
    client = TestClient(app)
    resp = client.get(f"/runs/{run_id}/cases/case_000")
    assert resp.status_code == 200
    body = resp.json()
    assert "trajectory" in body
    assert "verdicts" in body
    assert len(body["verdicts"]) == 3


def test_get_run_not_found():
    client = TestClient(app)
    resp = client.get("/runs/999")
    assert resp.status_code == 404


def test_list_agents():
    _seed_one_run()
    client = TestClient(app)
    resp = client.get("/agents")
    assert resp.status_code == 200
    data = resp.json()
    assert any(a["name"] == "api-test-agent" for a in data)


def test_list_benchmarks():
    _seed_one_run()
    client = TestClient(app)
    resp = client.get("/benchmarks")
    assert resp.status_code == 200
    data = resp.json()
    assert any(b["name"] == "api-test-bench" for b in data)


def test_compare():
    """Seed two runs with overlapping cases and verify compare response."""
    # First run
    run_a_id = _seed_one_run()

    # Second run with same case ids but different benchmark name
    cfg = AgentConfig(
        name="api-test-agent-v2",
        model="claude-haiku-4-5-20251001",
        system="sys",
        tools=[],
        max_steps=3,
    )
    spec = BenchmarkSpec(
        name="api-test-bench-v2",
        description="desc",
        cases=[
            BenchCase(
                id=f"case_{i:03d}",
                task=f"Task {i}",
                inputs={"user_message": f"msg {i}"},
            )
            for i in range(2)
        ],
    )
    traj = Trajectory(
        run_id="y",
        model="claude-haiku-4-5-20251001",
        system="sys",
        initial_messages=[{"role": "user", "content": "hi"}],
        final_response="done",
    )
    verdicts = [
        JudgeVerdict(
            judge="output", passed=False, score=0.5, rationale="ok", details={}
        ),
        JudgeVerdict(
            judge="trajectory", passed=False, score=0.5, rationale="ok", details={}
        ),
        JudgeVerdict(
            judge="rubric", passed=True, score=0.8, rationale="ok", details={}
        ),
    ]
    with Session(get_engine()) as session:
        agent_rec = upsert_agent(session, cfg)
        bm_rec = upsert_benchmark(session, spec)
        run_b = create_run(session, agent_rec.id, bm_rec.id, total_cases=2)
        for case in spec.cases:
            save_case_result(session, run_b.id, case, traj, verdicts)
        finalize_run(session, run_b.id)
        run_b_id = run_b.id

    client = TestClient(app)
    resp = client.get(f"/compare?a={run_a_id}&b={run_b_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert "cases" in body
    assert len(body["cases"]) == 2
    # delta should be negative (v2 scored lower)
    for diff in body["cases"]:
        assert "delta" in diff
        assert diff["delta"] < 0
