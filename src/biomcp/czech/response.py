"""Dual output formatting for Czech healthcare tools.

All Czech tools return JSON string with both human-readable
Markdown (`content`) and machine-readable dict (`structuredContent`)
per FR-025.
"""

import json


def format_czech_response(
    data: dict,
    tool_name: str,
    markdown_template: str | None = None,
) -> str:
    """Format tool output as dual content (Markdown + JSON).

    Args:
        data: Dict from Pydantic model_dump() or raw dict.
        tool_name: Tool identifier (e.g. "search_drug").
        markdown_template: Pre-formatted Markdown string.
            If None, auto-generates from data keys.

    Returns:
        JSON string with ``content`` and ``structuredContent``.
    """
    if markdown_template is not None:
        content = markdown_template
    else:
        content = _auto_markdown(data, tool_name)

    result = {
        "content": content,
        "structuredContent": {
            "type": tool_name,
            **data,
        },
    }
    return json.dumps(result, ensure_ascii=False)


def _auto_markdown(data: dict, tool_name: str) -> str:
    """Generate simple Markdown from dict keys."""
    title = tool_name.replace("_", " ").title()
    lines = [f"## {title}", ""]
    for key, value in data.items():
        if value is None:
            continue
        label = key.replace("_", " ").capitalize()
        if isinstance(value, list):
            lines.append(f"**{label}**: {len(value)} položek")
        elif isinstance(value, dict):
            lines.append(f"**{label}**: (objekt)")
        else:
            lines.append(f"**{label}**: {value}")
    return "\n".join(lines)
