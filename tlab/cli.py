import typer

app = typer.Typer(name="tlab", help="TrajectoryLab — agent eval harness.")


@app.command()
def run(
    benchmark: str = typer.Option(..., help="Path to benchmark folder"),
    agent: str = typer.Option(..., help="Path to agent YAML config"),
) -> None:
    """Run a benchmark suite against an agent config."""
    typer.echo("runner not yet implemented")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Bind host"),
    port: int = typer.Option(8000, help="Bind port"),
) -> None:
    """Start the TrajectoryLab API server."""
    typer.echo("API not yet implemented")
