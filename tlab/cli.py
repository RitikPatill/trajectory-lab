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
    from tlab.bench import load_agent, load_benchmark
    from tlab.runner import DEFAULT_HANDLERS, TOOL_DEFINITIONS, run_agent

    bench = load_benchmark(benchmark)
    cfg = load_agent(agent)

    tools = [t for t in TOOL_DEFINITIONS if t["name"] in cfg.tools]
    handlers = {k: v for k, v in DEFAULT_HANDLERS.items() if k in cfg.tools}

    typer.echo(f"Benchmark : {bench.name} ({len(bench.cases)} cases)")
    typer.echo(f"Agent     : {cfg.name} / {cfg.model}")
    typer.echo("")

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

    typer.echo("\nDone.")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Bind host"),
    port: int = typer.Option(8000, help="Bind port"),
) -> None:
    """Start the TrajectoryLab API server."""
    typer.echo("API not yet implemented")
