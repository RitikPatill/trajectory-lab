"""SQLite storage layer — M5."""

from tlab.storage.crud import (
    create_run,
    finalize_run,
    get_case_result,
    get_run,
    get_trajectory_record,
    list_agents,
    list_benchmarks,
    list_case_results,
    list_runs,
    list_verdicts,
    save_case_result,
    upsert_agent,
    upsert_benchmark,
)
from tlab.storage.engine import get_engine, get_session, reset_engine
from tlab.storage.models import (
    Agent,
    Benchmark,
    CaseResult,
    Run,
    TrajectoryRecord,
    Verdict,
)

__all__ = [
    # engine
    "get_engine",
    "get_session",
    "reset_engine",
    # models
    "Agent",
    "Benchmark",
    "CaseResult",
    "Run",
    "TrajectoryRecord",
    "Verdict",
    # crud
    "upsert_agent",
    "upsert_benchmark",
    "create_run",
    "save_case_result",
    "finalize_run",
    "list_runs",
    "get_run",
    "list_case_results",
    "get_case_result",
    "get_trajectory_record",
    "list_verdicts",
    "list_agents",
    "list_benchmarks",
]
