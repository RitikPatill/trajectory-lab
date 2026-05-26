"""Benchmark and agent config loaders."""

from __future__ import annotations

from pathlib import Path

import yaml

from tlab.bench.schema import AgentConfig, Benchmark


def load_benchmark(path: str | Path) -> Benchmark:
    """Load and validate a benchmark folder containing benchmark.yaml."""
    p = Path(path)
    yaml_file = p / "benchmark.yaml"
    if not yaml_file.exists():
        raise FileNotFoundError(f"benchmark.yaml not found in {path}")
    return Benchmark.model_validate(yaml.safe_load(yaml_file.read_text()))


def load_agent(path: str | Path) -> AgentConfig:
    """Load and validate an agent YAML config file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Agent config not found: {path}")
    return AgentConfig.model_validate(yaml.safe_load(p.read_text()))
