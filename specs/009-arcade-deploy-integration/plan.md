# Implementation Plan: Arcade Deploy Integration (Dual-Mode)

**Branch**: `009-arcade-deploy-integration` | **Date**: 2026-03-21 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-arcade-deploy-integration/spec.md`

## Summary

Deploy all 60 CzechMedMCP tools to the Arcade platform as a second distribution channel alongside Railway. The approach creates thin async wrapper functions in a new `src/czechmedmcp/arcade/` package that delegate to existing private implementation functions. Arcade SDK uses `@app.tool` with `Annotated[type, "description"]` annotations. A PoC with 5 tools validates platform compatibility before full 60-tool migration.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: FastMCP (existing), arcade-mcp-server (new, optional extra)
**Storage**: diskcache (shared, ephemeral on Arcade Cloud — lazy init handles cache misses)
**Testing**: pytest, pytest-xdist, pytest-asyncio
**Target Platform**: Arcade Cloud (deployment) + Railway (existing, unchanged)
**Project Type**: MCP server / library
**Performance Goals**: <10s latency per tool call on Arcade, deploy <10 minutes
**Constraints**: arcade-mcp is optional dependency; zero changes to existing FastMCP tools; no breaking changes to Railway deployment
**Scale/Scope**: 60 tools, PoC with 5 tools first, Hobby plan (1000 exec/month)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. MCP Protocol First | **PASS** | Arcade tools remain MCP-compliant (Arcade SDK implements MCP protocol). Tools are registered through Arcade's MCPApp which exposes MCP-standard interface. |
| II. Modular Domain Architecture | **PASS** | New `arcade/` package is independent module under `src/czechmedmcp/`. No changes to existing domain modules. Mirrors `czech/` namespace pattern. |
| III. Authoritative Data Sources | **PASS** | No new data sources. Arcade wrappers call same private functions → same APIs. |
| IV. CLI & MCP Dual Access | **PASS** | Arcade adds a third access path (Arcade Cloud) without removing CLI or FastMCP. CLI access unchanged. |
| V. Testing Rigor | **PASS** | FR-009 requires Arcade 60-tool count test. FR-010 preserves existing FastMCP test. Unit tests with mocked HTTP. |
| Technical Constraints | **PASS** | Python 3.10+, `arcade-mcp` optional in pyproject.toml, `ensure_ascii=False` preserved in wrappers. |
| Development Workflow | **PASS** | Feature branch via speckit, PR to main, conventional commits. |

**No violations. No complexity tracking needed.**

## Project Structure

### Documentation (this feature)

```text
specs/009-arcade-deploy-integration/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: Arcade SDK research
├── data-model.md        # Phase 1: Entity/wrapper mapping
├── quickstart.md        # Phase 1: Deployment quickstart
├── contracts/           # Phase 1: Tool wrapper contract
│   └── arcade-tool-contract.md
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
src/czechmedmcp/
├── arcade/                         # NEW: Arcade integration package
│   ├── __init__.py                 # arcade_app MCPApp singleton
│   ├── entrypoint.py               # Full 60-tool entrypoint (arcade deploy -e)
│   ├── poc_entrypoint.py           # PoC 5-tool entrypoint
│   ├── individual_tools.py         # 33 individual tool wrappers
│   ├── czech_tools.py              # 23 Czech tool wrappers
│   ├── router_tools.py             # 2 router tool wrappers (search + fetch)
│   ├── thinking_tool.py            # 1 think tool wrapper (dict→str)
│   └── metrics_tool.py             # 1 metrics tool wrapper
├── individual_tools.py             # UNCHANGED (33 FastMCP tools)
├── czech/czech_tools.py            # UNCHANGED (23 FastMCP tools)
├── router.py                       # UNCHANGED (2 FastMCP tools)
├── thinking_tool.py                # UNCHANGED (1 FastMCP tool)
├── metrics_handler.py              # UNCHANGED (1 FastMCP tool)
└── core.py                         # UNCHANGED (mcp_app singleton)

tests/
├── tdd/
│   ├── test_mcp_integration.py     # UNCHANGED (60-tool FastMCP test)
│   └── test_arcade_integration.py  # NEW: 60-tool Arcade count test
├── tdd/test_arcade_poc.py          # NEW: PoC 5-tool validation test
└── tdd/test_arcade_wrappers.py     # NEW: Wrapper behavior tests (constraints, dict→str)

pyproject.toml                       # MODIFIED: add [arcade] optional extra
```

**Structure Decision**: New `arcade/` package under `src/czechmedmcp/` following the modular domain pattern (Constitution Principle II). Entrypoint file is separate from app singleton to support both `arcade deploy -e` and `python -m` invocation.

## Implementation Phases

### Phase 1: Foundation (arcade/ package + optional dependency)

**Goal**: Create the `arcade/` package skeleton and optional dependency.

1. Add `arcade` optional extra to `pyproject.toml`:
   ```toml
   [project.optional-dependencies]
   arcade = ["arcade-mcp-server>=1.17.0"]
   ```
2. Create `src/czechmedmcp/arcade/__init__.py` with `arcade_app` MCPApp singleton
3. Verify `uv sync` (without arcade extra) still works — no import errors

### Phase 2: PoC Wrappers (5 tools)

**Goal**: Validate Arcade SDK compatibility with representative tools.

1. Create `arcade/individual_tools.py` with `article_searcher` + `article_getter` wrappers
2. Create `arcade/czech_tools.py` with `czechmed_search_medicine` wrapper
3. Create `arcade/thinking_tool.py` with `think` wrapper (dict→str serialization)
4. Create `arcade/metrics_tool.py` with `get_performance_metrics` wrapper
5. Create `arcade/poc_entrypoint.py` (5 tools, `if __name__ == "__main__": app.run()`)
6. Create `tests/tdd/test_arcade_poc.py` — validates PoC registers exactly 5 tools
7. Create `tests/tdd/test_arcade_wrappers.py` — tests constraint validation, dict→str

### Phase 3: Full Wrappers (60 tools)

**Goal**: Extend all remaining 55 tool wrappers.

1. Complete `arcade/individual_tools.py` — remaining 31 individual tool wrappers
2. Complete `arcade/czech_tools.py` — remaining 22 Czech tool wrappers
3. Create `arcade/router_tools.py` — `search` + `fetch` wrappers
4. Create `arcade/entrypoint.py` — full 60-tool entrypoint
5. Create `tests/tdd/test_arcade_integration.py` — validates exactly 60 Arcade tools

### Phase 4: Testing & Regression

**Goal**: Ensure zero regressions and full coverage.

1. Run existing test suite — all 1020+ tests pass unchanged
2. Run new Arcade tests — PoC, wrappers, integration
3. Verify FastMCP `test_mcp_integration.py` still asserts 60 tools
4. Verify `uv sync` without `[arcade]` extra → no import errors
5. Verify `uv sync --extra arcade` → Arcade entrypoint importable

### Phase 5: Documentation & CLAUDE.md

**Goal**: Document dual deployment and update developer instructions.

1. Update CLAUDE.md:
   - Add Arcade deployment section to Deployment table
   - Update "Adding a new tool" section with Arcade registration step
   - Add `arcade/` module descriptions to Key Files table
2. Create deployment documentation (markdown in `apps/docs/` or README section):
   - Railway vs Arcade trade-offs table
   - Step-by-step for each deployment option
   - PoC validation guide

## Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Arcade app location | `arcade/__init__.py` | Mirrors `core.py` pattern; separate from entrypoint for testability |
| Wrapper granularity | Per-source-module files | Maintains 1:1 mapping with FastMCP source files |
| Parameter types | Simplified to `str \| None` for list params | Arcade annotations don't support complex unions; `ensure_list()` handles internally |
| Constraint validation | Clamping (not raising) | User-friendly; matches MCP tool behavior expectations |
| PoC first | 5 tools before 60 | Risk reduction per spec requirement (FR, SC-007) |
| No @track_performance | Arcade wrappers skip it | Arcade has built-in observability; avoids dual metrics |

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| `arcade-mcp` conflicts with `mcp[cli]` | High | Optional extra isolation; tested in Phase 4 |
| Arcade Cloud ephemeral filesystem | Medium | Already handled by lazy init pattern in all tools |
| SUKL DrugIndex cold start timeout | Medium | Health endpoint returns before index build (lazy init) |
| Arcade SDK breaking changes | Low | Pinned version in pyproject.toml |
| 60 wrappers = maintenance burden | Medium | 1:1 mapping makes updates mechanical; test enforces count parity |

## Dependencies Between Phases

```
Phase 1 (Foundation) → Phase 2 (PoC) → Phase 3 (Full) → Phase 4 (Testing)
                                                        → Phase 5 (Docs)
```

Phase 4 and Phase 5 can run in parallel after Phase 3.
