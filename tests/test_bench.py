"""Tests for benchmark loader — no live API calls required."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from tlab.bench import load_agent, load_benchmark
from tlab.bench.schema import (
    BenchCase,
    OutputValidator,
    Rubric,
    RubricCriterion,
)

REPO = Path(__file__).parent.parent


def test_load_research_benchmark():
    b = load_benchmark(REPO / "benchmarks" / "research")
    assert b.name == "research"
    assert len(b.cases) == 10


def test_load_calculator_benchmark():
    b = load_benchmark(REPO / "benchmarks" / "calculator")
    assert b.name == "calculator"
    assert len(b.cases) == 10


def test_load_agent_research():
    cfg = load_agent(REPO / "agents" / "research_v1.yaml")
    assert cfg.name == "research_v1"
    assert "web_search" in cfg.tools


def test_load_agent_calculator():
    cfg = load_agent(REPO / "agents" / "calculator_v1.yaml")
    assert cfg.name == "calculator_v1"
    assert "calculator" in cfg.tools


def test_missing_benchmark_folder():
    with pytest.raises(FileNotFoundError):
        load_benchmark(REPO / "benchmarks" / "nonexistent")


def test_missing_agent_file():
    with pytest.raises(FileNotFoundError):
        load_agent(REPO / "agents" / "ghost_agent.yaml")


def test_bench_case_missing_id():
    with pytest.raises(ValidationError):
        BenchCase.model_validate(
            {"task": "no id here", "inputs": {"user_message": "hi"}}
        )


def test_output_validator_invalid_type():
    with pytest.raises(ValidationError):
        OutputValidator.model_validate({"type": "unknown", "value": "something"})


def test_rubric_defaults():
    criterion = RubricCriterion.model_validate({"id": "c1", "description": "test"})
    assert criterion.weight == 1.0

    rubric = Rubric.model_validate(
        {"criteria": [{"id": "c1", "description": "test"}]}
    )
    assert rubric.pass_threshold == 0.7


def test_case_inputs_preserved():
    data = {
        "id": "x1",
        "task": "some task",
        "inputs": {"user_message": "hello", "context": "extra data", "num": 42},
    }
    case = BenchCase.model_validate(data)
    assert case.inputs["user_message"] == "hello"
    assert case.inputs["context"] == "extra data"
    assert case.inputs["num"] == 42
