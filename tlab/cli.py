"""TrajectoryLab CLI entry point."""

from __future__ import annotations

import typer

app = typer.Typer(name="tlab", help="TrajectoryLab — agent eval harness.")


@app.command()
def run(
    benchmark: str = typer.Option(..., help="Path to benchmark folder"),
    agent: str = typer.Option(..., help="Path to agent YAML config"),
) -> None:
    """Run a benchmark suite against an agent config."""
    import anthropic as _anthropic
    from sqlmodel import Session

    from tlab.bench import load_agent, load_benchmark
    from tlab.judges import OutputJudge, RubricJudge, TrajectoryJudge
    from tlab.runner import DEFAULT_HANDLERS, TOOL_DEFINITIONS, run_agent
    from tlab.storage import (
        create_run,
        finalize_run,
        get_engine,
        save_case_result,
        upsert_agent,
        upsert_benchmark,
    )

    bench = load_benchmark(benchmark)
    cfg = load_agent(agent)

    tools = [t for t in TOOL_DEFINITIONS if t["name"] in cfg.tools]
    handlers = {k: v for k, v in DEFAULT_HANDLERS.items() if k in cfg.tools}

    typer.echo(f"Benchmark : {bench.name} ({len(bench.cases)} cases)")
    typer.echo(f"Agent     : {cfg.name} / {cfg.model}")
    typer.echo("")

    client = _anthropic.Anthropic()
    rubric_judge = RubricJudge(client=client)
    traj_judge = TrajectoryJudge()
    out_judge = OutputJudge()

    with Session(get_engine()) as session:
        agent_rec = upsert_agent(session, cfg)
        bm_rec = upsert_benchmark(session, bench)
        run_rec = create_run(session, agent_rec.id, bm_rec.id, len(bench.cases))

        for case in bench.cases:
            typer.echo(f"  [{case.id}] {case.task[:60]}")
            user_msg = case.inputs.get("user_message", case.task)
            traj = run_agent(
                system=cfg.system,
                messages=[{"role": "user", "content": user_msg}],
                tools=tools,
                tool_handlers=handlers,
                model=cfg.model,
                max_steps=cfg.max_steps,
            )
            status = "ERROR" if traj.error else "ok"
            typer.echo(
                f"         {status} — {len(traj.steps)} steps  "
                f"{traj.total_input_tokens}in/{traj.total_output_tokens}out tok"
            )

            verdicts = [
                out_judge.judge(traj, case),
                traj_judge.judge(traj, case),
                rubric_judge.judge(traj, case),
            ]
            cr = save_case_result(session, run_rec.id, case, traj, verdicts)
            result_icon = "PASS" if cr.passed else "FAIL"
            typer.echo(f"         {result_icon} — score={cr.aggregate_score:.2f}")

        finalize_run(session, run_rec.id)

    typer.echo(
        f"\nRun #{run_rec.id} — {run_rec.passed_cases}/{run_rec.total_cases} passed"
    )
    typer.echo("Done.")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Bind host"),
    port: int = typer.Option(8000, help="Bind port"),
) -> None:
    """Start the TrajectoryLab API server."""
    import uvicorn

    from tlab.api import app as fastapi_app

    uvicorn.run(fastapi_app, host=host, port=port)
