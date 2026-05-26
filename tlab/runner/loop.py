"""Agent runner loop with trajectory capture."""

from __future__ import annotations

import copy
import time
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import uuid4

import anthropic

from tlab.runner.trace import Step, ToolCall, ToolResult, Trajectory


def run_agent(
    *,
    system: str,
    messages: list[dict],
    tools: list[dict],
    tool_handlers: dict[str, Callable[..., str]],
    model: str = "claude-haiku-4-5-20251001",
    max_steps: int = 10,
    client: anthropic.Anthropic | None = None,
) -> Trajectory:
    """Run the agent loop and return a fully-captured Trajectory."""
    if client is None:
        client = anthropic.Anthropic()

    working_messages = copy.deepcopy(messages)
    trajectory = Trajectory(
        run_id=uuid4().hex,
        model=model,
        system=system,
        initial_messages=copy.deepcopy(messages),
        created_at=datetime.now(UTC),
    )

    step_index = 0

    for _ in range(max_steps):
        t0 = time.monotonic()
        response = client.messages.create(
            model=model,
            system=system,
            messages=working_messages,
            tools=tools,  # type: ignore[arg-type]
            max_tokens=4096,
        )
        latency_ms = (time.monotonic() - t0) * 1000

        raw_content = [b.model_dump() for b in response.content]
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        # Collect tool calls from this assistant response
        tool_calls: list[ToolCall] = []
        for block in response.content:
            if block.type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        tool_use_id=block.id,
                        name=block.name,
                        input=block.input,
                    )
                )

        trajectory.steps.append(
            Step(
                index=step_index,
                role="assistant",
                raw_content=raw_content,
                tool_calls=tool_calls,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                timestamp=datetime.now(UTC),
            )
        )
        step_index += 1

        trajectory.total_input_tokens += input_tokens
        trajectory.total_output_tokens += output_tokens
        trajectory.total_latency_ms += latency_ms

        # Append assistant message to working list
        working_messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            # Extract final text response
            for block in response.content:
                if block.type == "text":
                    trajectory.final_response = block.text
                    break
            break

        if response.stop_reason == "tool_use":
            tool_results: list[ToolResult] = []
            tool_result_dicts: list[dict] = []

            for block in response.content:
                if block.type != "tool_use":
                    continue
                handler = tool_handlers.get(block.name)
                if handler is None:
                    result_content = f"Error: unknown tool '{block.name}'"
                    is_error = True
                else:
                    try:
                        result_content = handler(**block.input)
                        is_error = False
                    except Exception as exc:
                        result_content = f"Error: {exc}"
                        is_error = True

                tool_results.append(
                    ToolResult(
                        tool_use_id=block.id,
                        name=block.name,
                        content=result_content,
                        is_error=is_error,
                    )
                )
                tool_result_dicts.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_content,
                    }
                )

            trajectory.steps.append(
                Step(
                    index=step_index,
                    role="tool",
                    raw_content=tool_result_dicts,
                    tool_results=tool_results,
                    timestamp=datetime.now(UTC),
                )
            )
            step_index += 1

            working_messages.append({"role": "user", "content": tool_result_dicts})
            continue

        # Unknown stop reason
        trajectory.error = f"unexpected stop_reason: {response.stop_reason}"
        break
    else:
        trajectory.error = "max_steps exceeded"

    return trajectory
