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
def compare(
    run_a: int = typer.Argument(..., help="First run ID"),
    run_b: int = typer.Argument(..., help="Second run ID"),
) -> None:
    """Print a per-case comparison between two runs."""
    from sqlmodel import Session, select

    from tlab.storage import CaseResult, get_engine

    with Session(get_engine()) as session:
        cases_a = {
            cr.case_id: cr
            for cr in session.exec(
                select(CaseResult).where(CaseResult.run_id == run_a)
            ).all()
        }
        cases_b = {
            cr.case_id: cr
            for cr in session.exec(
                select(CaseResult).where(CaseResult.run_id == run_b)
            ).all()
        }

    shared_ids = sorted(set(cases_a.keys()) & set(cases_b.keys()))
    if not shared_ids:
        typer.echo(f"No shared cases between run {run_a} and run {run_b}.")
        raise typer.Exit(1)

    typer.echo(f"Comparing Run #{run_a} vs Run #{run_b}")
    typer.echo("")
    header = f"{'Case':<20} {'Score A':>8} {'Score B':>8} {'Delta':>8}  Status"
    typer.echo(header)
    typer.echo("-" * len(header))

    improved = regressed = unchanged = 0
    total_delta = 0.0

    for cid in shared_ids:
        sa = cases_a[cid].aggregate_score
        sb = cases_b[cid].aggregate_score
        delta = sb - sa
        total_delta += delta
        if delta > 0.001:
            status = "IMPROVED"
            improved += 1
        elif delta < -0.001:
            status = "REGRESSED"
            regressed += 1
        else:
            status = "UNCHANGED"
            unchanged += 1
        sign = "+" if delta >= 0 else ""
        typer.echo(
            f"{cid:<20} {sa*100:>7.1f}% {sb*100:>7.1f}% {sign}{delta*100:>6.1f}%  {status}"
        )

    mean_delta = total_delta / len(shared_ids) if shared_ids else 0.0
    sign = "+" if mean_delta >= 0 else ""
    typer.echo("")
    typer.echo(
        f"Improved: {improved}  Regressed: {regressed}  Unchanged: {unchanged}"
        f"  Mean delta: {sign}{mean_delta*100:.2f}%"
    )


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Bind host"),
    port: int = typer.Option(8000, help="Bind port"),
) -> None:
    """Start the TrajectoryLab API server."""
    import uvicorn

    from tlab.api import app as fastapi_app

    uvicorn.run(fastapi_app, host=host, port=port)
