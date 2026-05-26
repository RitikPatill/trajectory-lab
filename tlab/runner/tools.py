"""Mock tool handlers and Anthropic tool definition dicts."""

from __future__ import annotations

from collections.abc import Callable


def web_search(query: str) -> str:
    """Return a mock web search result."""
    return f"[mock web_search] Results for: {query}"


def calculator(expression: str) -> str:
    """Evaluate a safe arithmetic expression."""
    allowed = set("0123456789+-*/()., ")
    if not all(c in allowed for c in expression):
        return "Error: unsafe expression"
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))  # noqa: S307
    except Exception as exc:
        return f"Error: {exc}"


TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "web_search",
        "description": "Search the web for information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"],
        },
    },
    {
        "name": "calculator",
        "description": "Evaluate a safe arithmetic expression.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Arithmetic expression",
                }
            },
            "required": ["expression"],
        },
    },
]

DEFAULT_HANDLERS: dict[str, Callable] = {
    "web_search": web_search,
    "calculator": calculator,
}
