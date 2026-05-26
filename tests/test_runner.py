"""Tests for tlab.runner — no live API calls."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from tlab.runner import run_agent
from tlab.runner.tools import calculator, web_search

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _text_block(text: str) -> SimpleNamespace:
    return SimpleNamespace(
        type="text",
        text=text,
        model_dump=lambda: {"type": "text", "text": text},
    )


def _tool_use_block(tool_use_id: str, name: str, input: dict) -> SimpleNamespace:
    return SimpleNamespace(
        type="tool_use",
        id=tool_use_id,
        name=name,
        input=input,
        model_dump=lambda: {
            "type": "tool_use",
            "id": tool_use_id,
            "name": name,
            "input": input,
        },
    )


def _usage(input_tokens: int = 10, output_tokens: int = 5) -> SimpleNamespace:
    return SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens)


def _response(stop_reason: str, content: list, usage=None) -> MagicMock:
    r = MagicMock()
    r.stop_reason = stop_reason
    r.content = content
    r.usage = usage or _usage()
    return r


def _mock_client(*responses) -> MagicMock:
    client = MagicMock()
    client.messages.create.side_effect = list(responses)
    return client


# ---------------------------------------------------------------------------
# Test 1 — calculator tool directly
# ---------------------------------------------------------------------------


def test_calculator_basic():
    assert calculator("2 + 2") == "4"


def test_calculator_division():
    assert calculator("10 / 4") == "2.5"


def test_calculator_blocks_unsafe():
    result = calculator("__import__('os')")
    assert result == "Error: unsafe expression"


# ---------------------------------------------------------------------------
# Test 2 — web_search tool directly
# ---------------------------------------------------------------------------


def test_web_search_contains_query():
    result = web_search("climate change")
    assert "climate change" in result


# ---------------------------------------------------------------------------
# Test 3 — single end_turn response (no tools)
# ---------------------------------------------------------------------------


def test_end_turn_no_tools():
    mock_client = _mock_client(
        _response("end_turn", [_text_block("Hello")], _usage(10, 5))
    )

    traj = run_agent(
        system="You are a helpful assistant.",
        messages=[{"role": "user", "content": "hi"}],
        tools=[],
        tool_handlers={},
        client=mock_client,
    )

    assert traj.final_response == "Hello"
    assert len(traj.steps) == 1
    assert traj.steps[0].role == "assistant"
    assert traj.total_input_tokens == 10
    assert traj.total_output_tokens == 5


# ---------------------------------------------------------------------------
# Test 4 — one tool call then end_turn
# ---------------------------------------------------------------------------


def test_tool_call_then_end_turn():
    tool_block = _tool_use_block("tu_001", "calculator", {"expression": "1+1"})
    final_text = _text_block("The answer is 2")

    mock_client = _mock_client(
        _response("tool_use", [tool_block], _usage(20, 10)),
        _response("end_turn", [final_text], _usage(30, 8)),
    )

    traj = run_agent(
        system="You are a calculator assistant.",
        messages=[{"role": "user", "content": "What is 1+1?"}],
        tools=[],
        tool_handlers={"calculator": calculator},
        client=mock_client,
    )

    assert traj.final_response == "The answer is 2"
    # step 0: assistant (tool_use), step 1: tool results, step 2: assistant (end_turn)
    assert len(traj.steps) == 3
    assert traj.steps[0].role == "assistant"
    assert traj.steps[0].tool_calls[0].name == "calculator"
    assert traj.steps[1].role == "tool"
    assert traj.steps[1].tool_results[0].content == "2"
    assert traj.steps[2].role == "assistant"


# ---------------------------------------------------------------------------
# Test 5 — max_steps guard
# ---------------------------------------------------------------------------


def test_max_steps_exceeded():
    tool_block = _tool_use_block("tu_loop", "calculator", {"expression": "1+1"})
    always_tool = _response("tool_use", [tool_block], _usage(5, 5))

    mock_client = MagicMock()
    mock_client.messages.create.return_value = always_tool

    traj = run_agent(
        system="You are a loopy assistant.",
        messages=[{"role": "user", "content": "loop"}],
        tools=[],
        tool_handlers={"calculator": calculator},
        max_steps=2,
        client=mock_client,
    )

    assert traj.error == "max_steps exceeded"
    # 2 assistant steps + 2 tool steps = 4 steps recorded before guard fires
    assert mock_client.messages.create.call_count == 2
