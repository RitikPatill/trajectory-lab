"""Seed the TrajectoryLab demo database with two canned runs."""

import json
import os
import sys
from pathlib import Path

# Append repo root so tlab is importable without install
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, SQLModel, select  # noqa: E402

from tlab.runner.trace import Step, ToolCall, ToolResult, Trajectory  # noqa: E402
from tlab.storage.engine import get_engine, reset_engine  # noqa: E402
from tlab.storage.models import (  # noqa: E402
    Agent,
    Benchmark,
    CaseResult,
    Run,
    TrajectoryRecord,
    Verdict,
)

CASE_IDS = [f"research_{i:03d}" for i in range(1, 11)]
TASKS = [
    "What is the capital of France?",
    "What is the population of Germany?",
    "Who invented the telephone?",
    "What is the boiling point of water in Fahrenheit?",
    "When did World War 2 end?",
    "What is the speed of light in meters per second?",
    "Who wrote Romeo and Juliet?",
    "What is the largest planet in our solar system?",
    "What is the chemical symbol for gold?",
    "In what year did the Berlin Wall fall?",
]
ANSWERS = [
    "Paris",
    "84 million",
    "Bell",
    "212°F",
    "1945",
    "299,792,458 m/s",
    "Shakespeare",
    "Jupiter",
    "Au",
    "1989",
]

# v1 passes 6/10; v2 passes 8/10
# case indices that each agent passes (0-indexed)
V1_PASS = {0, 2, 3, 5, 6, 8}  # 6 passes
# 8 passes (regression on 6,9; improvements on 1,4,7)
V2_PASS = {0, 1, 2, 3, 4, 5, 7, 8}


def make_trajectory(
    case_id: str, task: str, answer: str, model: str, passed: bool
) -> str:
    """Build a Trajectory and return its JSON string."""
    tool_call = ToolCall(
        tool_use_id=f"tu_{case_id}",
        name="web_search",
        input={"query": task},
    )
    tool_result = ToolResult(
        tool_use_id=f"tu_{case_id}",
        name="web_search",
        content=f"[mock web_search] Results for: {task}",
    )
    step0 = Step(
        index=0,
        role="assistant",
        raw_content=[
            {
                "type": "tool_use",
                "id": f"tu_{case_id}",
                "name": "web_search",
                "input": {"query": task},
            }
        ],
        tool_calls=[tool_call],
        input_tokens=120,
        output_tokens=40,
        latency_ms=450.0,
    )
    step1 = Step(
        index=1,
        role="tool",
        raw_content=[
            {
                "type": "tool_result",
                "tool_use_id": f"tu_{case_id}",
                "content": tool_result.content,
            }
        ],
        tool_results=[tool_result],
        input_tokens=0,
        output_tokens=0,
        latency_ms=5.0,
    )
    traj = Trajectory(
        run_id=case_id,
        model=model,
        system="You are a research assistant.",
        initial_messages=[{"role": "user", "content": task}],
        steps=[step0, step1],
        final_response=answer if passed else "I could not find that information.",
        error=None,
        total_input_tokens=120,
        total_output_tokens=40,
        total_latency_ms=455.0,
    )
    return traj.model_dump_json()


def seed_run(
    session: Session,
    agent_id: int,
    bm_id: int,
    pass_set: set,
    model: str,
) -> None:
    run = Run(
        agent_id=agent_id,
        benchmark_id=bm_id,
        total_cases=10,
        passed_cases=len(pass_set),
        mean_score=round(len(pass_set) / 10, 2),
    )
    session.add(run)
    session.commit()
    session.refresh(run)

    for i, (case_id, task, answer) in enumerate(zip(CASE_IDS, TASKS, ANSWERS)):
        passed = i in pass_set
        score = 1.0 if passed else 0.0
        cr = CaseResult(
            run_id=run.id,
            case_id=case_id,
            task=task,
            inputs_json=json.dumps({"user_message": task}),
            passed=passed,
            aggregate_score=score,
        )
        session.add(cr)
        session.commit()
        session.refresh(cr)

        traj_json = make_trajectory(case_id, task, answer, model, passed)
        session.add(TrajectoryRecord(case_result_id=cr.id, data_json=traj_json))

        # output judge
        session.add(
            Verdict(
                case_result_id=cr.id,
                judge="output",
                passed=passed,
                score=score,
                rationale=(
                    "Response contains expected string."
                    if passed
                    else "Expected string not found."
                ),
                details_json=json.dumps(
                    {
                        "type": "contains",
                        "value": answer.split()[0],
                        "passed": passed,
                    }
                ),
            )
        )
        # trajectory judge
        session.add(
            Verdict(
                case_result_id=cr.id,
                judge="trajectory",
                passed=passed,
                score=score,
                rationale=(
                    "web_search was called."
                    if passed
                    else "web_search not called within max_steps."
                ),
                details_json=json.dumps(
                    {
                        "expected_tools_called": passed,
                        "max_steps_ok": True,
                        "error_loop_detected": False,
                        "step_count": 2,
                    }
                ),
            )
        )
        # rubric judge
        session.add(
            Verdict(
                case_result_id=cr.id,
                judge="rubric",
                passed=passed,
                score=score,
                rationale=(
                    "Answer is factually correct."
                    if passed
                    else "Answer is incomplete or missing."
                ),
                details_json=json.dumps(
                    {
                        "criteria": [
                            {
                                "criterion_id": "correct_answer",
                                "score": score,
                                "rationale": "Correct." if passed else "Incorrect.",
                            }
                        ]
                    }
                ),
            )
        )
        session.commit()


def main() -> None:
    db_path = os.environ.get("TLAB_DB", str(Path.home() / ".tlab" / "demo.db"))
    os.environ["TLAB_DB"] = db_path
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    # Reset any cached engine so TLAB_DB is picked up
    reset_engine()
    engine = get_engine()

    # Guard: skip if already seeded
    with Session(engine) as session:
        if session.exec(select(Agent)).first() is not None:
            print("DB already seeded — delete the DB file to re-seed.")
            print(f"  DB path: {db_path}")
            return

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        v1 = Agent(
            name="research_v1",
            model="claude-haiku-4-5-20251001",
            system="You are a research assistant. Use web_search to look up facts.",
            tools_json='["web_search"]',
            max_steps=5,
        )
        v2 = Agent(
            name="research_v2",
            model="claude-haiku-4-5-20251001",
            system=(
                "You are a concise research assistant. "
                "Call web_search once, then answer in one sentence."
            ),
            tools_json='["web_search"]',
            max_steps=8,
        )
        session.add(v1)
        session.add(v2)
        session.commit()
        session.refresh(v1)
        session.refresh(v2)

        bm = Benchmark(
            name="research",
            description="Factual look-up tasks requiring web_search.",
            case_count=10,
        )
        session.add(bm)
        session.commit()
        session.refresh(bm)

        seed_run(session, v1.id, bm.id, V1_PASS, v1.model)
        seed_run(session, v2.id, bm.id, V2_PASS, v2.model)

    print(f"Seeded demo DB at {db_path} — 2 runs, 10 cases each.")


if __name__ == "__main__":
    main()
