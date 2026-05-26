"""Pydantic models for trajectory capture."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    tool_use_id: str
    name: str
    input: dict[str, Any]


class ToolResult(BaseModel):
    tool_use_id: str
    name: str
    content: str
    is_error: bool = False


class Step(BaseModel):
    index: int
    role: Literal["assistant", "tool"]
    raw_content: list[dict[str, Any]]
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_results: list[ToolResult] = Field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Trajectory(BaseModel):
    run_id: str
    model: str
    system: str
    initial_messages: list[dict[str, Any]]
    steps: list[Step] = Field(default_factory=list)
    final_response: str | None = None
    error: str | None = None
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_latency_ms: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
