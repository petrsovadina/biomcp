# Arcade Tool Wrapper Contract

## Pattern

Every Arcade tool wrapper MUST follow this contract:

```python
@arcade_app.tool
async def <tool_name>(
    param1: Annotated[<type>, "<description>"],
    param2: Annotated[<type>, "<description>"] = <default>,
) -> str:
    """<Same docstring as FastMCP version>"""
    # 1. Validate constraints (if any ge/le/min_length/max_length)
    # 2. Transform parameters (ensure_list, type coercion)
    # 3. Call private implementation
    result = await _private_impl(param1, param2)
    # 4. Ensure str return
    return result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
```

## Rules

1. **Name**: Same as FastMCP tool name (e.g., `article_searcher`, `czechmed_search_medicine`)
2. **Docstring**: Same as FastMCP version (Arcade uses docstring for tool description)
3. **Parameters**: Same names and defaults; annotations simplified to `Annotated[type, "desc"]`
4. **Union types**: `list[str] | str | None` → `str | None` with `ensure_list()` internally
5. **Constraints**: `Field(ge=1, le=100)` → manual validation with clamping
6. **Return type**: Always `str`
7. **No @track_performance**: Arcade wrappers skip performance tracking (Arcade has its own observability)
8. **No import side effects**: Modules only register tools, no global state mutation

## Validation Mapping

| Pydantic Constraint | Arcade Wrapper Handling |
|---------------------|----------------------|
| `ge=1` | `param = max(1, param)` |
| `le=100` | `param = min(100, param)` |
| `min_length=1` | `if not param: return "Error: ..."` |
| `max_length=N` | `param = param[:N]` |
