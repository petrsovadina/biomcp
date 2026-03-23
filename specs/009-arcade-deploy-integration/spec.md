# Feature Specification: Arcade Deploy Integration (Dual-Mode)

**Feature Branch**: `009-arcade-deploy-integration`
**Created**: 2026-03-21
**Status**: Draft
**Input**: User description: "Dual-mode Arcade Deploy integration: deploy CzechMedMCP tools to Arcade platform while preserving Railway deployment as alternative"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Deploy CzechMedMCP to Arcade Platform (Priority: P1)

As a project maintainer, I want to deploy all 60 CzechMedMCP tools to the Arcade platform so that AI agents using Arcade can access Czech biomedical research tools through the Arcade tool catalog.

**Why this priority**: This is the core value proposition — making CzechMedMCP available on a new distribution platform that handles auth, discovery, and multi-user access out of the box.

**Independent Test**: Can be fully tested by running `arcade deploy` and verifying all 60 tools appear in the Arcade dashboard, each callable with correct parameters and returning expected results.

**Acceptance Scenarios**:

1. **Given** the Arcade entrypoint file exists with all 60 tools registered, **When** I run `arcade deploy -e <entrypoint>`, **Then** the deployment succeeds and all 60 tools are visible in the Arcade dashboard.
2. **Given** the server is deployed on Arcade, **When** an AI agent calls `article_searcher` with valid parameters, **Then** it returns PubMed search results in the expected format.
3. **Given** the server is deployed on Arcade, **When** an AI agent calls `czechmed_search_medicine` with query "ibuprofen", **Then** it returns SUKL drug registry results.
4. **Given** the Arcade deployment is running, **When** I check the health status in the Arcade dashboard, **Then** it shows "healthy".

---

### User Story 2 - Preserve Railway Deployment (Priority: P1)

As a project maintainer, I want the existing Railway deployment (FastMCP + Docker) to continue working unchanged so that current users and integrations (Claude Desktop STDIO, Railway HTTP endpoint) are not disrupted.

**Why this priority**: Breaking existing deployments would affect current users. Railway remains the primary, self-hosted deployment option with persistent storage and full control.

**Independent Test**: Can be fully tested by running `uv run czechmedmcp run --mode streamable_http` and verifying all 60 tools work identically to before the Arcade integration.

**Acceptance Scenarios**:

1. **Given** the Arcade integration code exists in the repository, **When** I run `uv run czechmedmcp run --mode stdio`, **Then** the STDIO server starts with all 60 tools, identical to pre-integration behavior.
2. **Given** the Arcade integration code exists, **When** I deploy to Railway via Docker, **Then** the Streamable HTTP server starts successfully with all 60 tools.
3. **Given** no Arcade SDK is installed (optional dependency), **When** I run the standard MCP server, **Then** it works without errors or Arcade-related import failures.

---

### User Story 3 - Validate with PoC Before Full Migration (Priority: P1)

As a project maintainer, I want to first deploy a small subset of tools (3-5) to Arcade as a proof-of-concept so that I can verify platform compatibility before migrating all 60 tools.

**Why this priority**: Reduces risk by validating assumptions (diskcache persistence, SUKL cold start, latency) before committing to full migration.

**Independent Test**: Can be tested by deploying a minimal entrypoint with article_searcher, czechmed_search_medicine, and think tools, then calling each through Arcade.

**Acceptance Scenarios**:

1. **Given** a PoC entrypoint with 3-5 tools, **When** I deploy to Arcade Hobby plan, **Then** the deployment succeeds within 5 minutes.
2. **Given** the PoC is deployed, **When** I call `article_searcher` with a PubMed query, **Then** results are returned with acceptable latency (under 10 seconds).
3. **Given** the PoC is deployed, **When** I call `czechmed_search_medicine` (which uses diskcache), **Then** the tool works and caching behavior is observable.
4. **Given** the PoC validation succeeds, **When** I extend the entrypoint to all 60 tools, **Then** the full deployment also succeeds.

---

### User Story 4 - Clear Deployment Choice Documentation (Priority: P2)

As a developer or contributor, I want clear documentation explaining both deployment options (Railway vs Arcade) so that I can choose the right deployment method based on my needs and understand the trade-offs.

**Why this priority**: Without clear documentation, users may not know about Arcade as an option or may accidentally break Railway setup trying to use Arcade features.

**Independent Test**: Can be tested by giving the documentation to a new developer and asking them to deploy to either platform following only the written instructions.

**Acceptance Scenarios**:

1. **Given** I read the deployment documentation, **When** I follow the Railway instructions, **Then** I can deploy successfully without any Arcade-related steps.
2. **Given** I read the deployment documentation, **When** I follow the Arcade instructions, **Then** I can deploy to Arcade successfully.
3. **Given** the documentation exists, **When** I compare both options, **Then** the trade-offs (persistence, auth, cost, data residency) are clearly listed.

---

### User Story 5 - Add New Tools to Both Platforms (Priority: P3)

As a developer adding a new tool to CzechMedMCP, I want a clear process for registering the tool on both platforms so that new tools are automatically available on Railway and Arcade.

**Why this priority**: Maintainability — without a clear process, new tools might be registered on one platform but forgotten on the other.

**Independent Test**: Can be tested by following the documented process to add a dummy test tool and verifying it appears on both platforms.

**Acceptance Scenarios**:

1. **Given** I create a new tool following the existing pattern, **When** I register it in both the FastMCP and Arcade tool files, **Then** the total tool count increases by 1 on both platforms.
2. **Given** the CLAUDE.md contains updated instructions, **When** I read the "Adding a new tool" section, **Then** it mentions both FastMCP and Arcade registration steps.

---

### Edge Cases

- What happens when Arcade Cloud restarts and diskcache SQLite files are lost? Tools must gracefully rebuild cache (already handled by lazy init pattern).
- What happens when SUKL DrugIndex cold start exceeds Arcade's deploy health-check timeout? The health endpoint must return "healthy" before the index is built (lazy init).
- What happens when a developer installs `arcade-mcp` but runs the FastMCP server? No side effects — Arcade code is isolated in separate modules.
- What happens when the `think()` tool returns `dict` instead of `str`? The Arcade adapter must serialize to JSON string.
- What happens when Arcade SDK has a breaking update? Pinned version in `pyproject.toml` prevents unexpected breakage.
- What happens when `arcade-mcp` and `mcp[cli]` packages conflict? Dependency isolation via optional extras prevents this.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide an Arcade-compatible entrypoint file that registers all 60 tools using the `arcade_mcp_server.MCPApp` API.
- **FR-002**: System MUST preserve all existing FastMCP tool registrations unchanged (in `individual_tools.py`, `czech_tools.py`, `thinking_tool.py`, `metrics_handler.py`, `router.py`).
- **FR-003**: The Arcade entrypoint MUST be deployable via `arcade deploy -e <path>` from the project root directory.
- **FR-004**: System MUST declare `arcade-mcp` as an optional dependency (not required for Railway/FastMCP operation).
- **FR-005**: All 60 Arcade tool wrappers MUST call the same private implementation functions (`_article_searcher`, `_sukl_drug_search`, etc.) as their FastMCP counterparts.
- **FR-006**: Tool parameter descriptions and types in Arcade registrations MUST match the semantics of the FastMCP versions (parameter names, types, defaults, descriptions).
- **FR-007**: Tools returning `dict` (specifically `think()`) MUST be adapted to return `str` (JSON serialized) in the Arcade registration.
- **FR-008**: The Arcade entrypoint MUST include `if __name__ == "__main__": app.run()` for Arcade Deploy validation.
- **FR-009**: System MUST include a regression test verifying that the Arcade entrypoint registers exactly 60 tools.
- **FR-010**: System MUST include a regression test verifying that the FastMCP server still registers exactly 60 tools (unchanged from current `test_mcp_integration.py`).
- **FR-011**: Documentation MUST describe both deployment options with a trade-offs table covering persistence, auth model, cost, data residency, and monitoring.
- **FR-012**: CLAUDE.md MUST be updated with instructions for adding new tools to both platforms.
- **FR-013**: Pydantic `Field` constraints (`ge`, `le`, `min_length`, `max_length`) not natively supported by Arcade annotations MUST be enforced via validation inside the Arcade wrapper functions.

### Key Entities

- **Arcade MCPApp**: The Arcade SDK application singleton, parallel to existing FastMCP `mcp_app` singleton. Created in the Arcade entrypoint module.
- **Tool Wrapper**: A thin async function registered with `@app.tool` that delegates to the existing private implementation function. One per tool, 60 total.
- **Arcade Entrypoint**: A Python module that creates the MCPApp, imports and registers all tools, and exposes `app.run()` for Arcade Deploy.

## Clarifications

### Session 2026-03-21

- Q: Ochrana zdravotnických dat na Arcade Cloud (data collection) → A: Pro MVP/free uživatele akceptovat Arcade data collection as-is — dotazy nejsou osobní zdravotní data. Pro enterprise a citlivé scénáře bude k dispozici Railway deployment bez Arcade. Rozlišení bude řešeno v budoucí verzi, ne v tomto MVP.

## Assumptions

- Arcade SDK (`arcade-mcp`) supports async tool functions natively.
- Arcade Cloud filesystem is ephemeral (no persistent diskcache between redeploys) — tools must handle cache misses gracefully (already the case with lazy init).
- The Arcade Hobby plan (free, 1000 executions/month) is sufficient for PoC validation.
- Arcade Deploy health-check timeout accommodates a server that returns "healthy" before SUKL DrugIndex is built.
- No tools require Arcade's OAuth per-tool authentication (all external APIs are public or use optional API keys passed as parameters).
- `arcade-mcp` package can coexist with `mcp[cli]>=1.12.3` without dependency conflicts.
- Arcade's `Annotated[type, "description"]` pattern is compatible with CzechMedMCP's existing parameter semantics.
- Arcade data collection is acceptable for MVP/free-tier users — tool queries (drug names, diagnosis codes, gene symbols) are not personal health records. Enterprise deployments requiring data isolation will use Railway exclusively.

## Out of Scope

- Migrating away from Railway — Railway remains the primary deployment.
- Adding Arcade OAuth per-tool authentication for external APIs.
- Rebuilding the HTTP client layer or cache infrastructure for Arcade.
- Creating an Arcade MCP Gateway (this spec uses native Arcade Deploy).
- UI changes to the landing page or documentation site.
- CI/CD pipeline changes for automatic Arcade deployment (can be added later).
- Changes to existing FastMCP tool implementations or their private functions.
- Enterprise data privacy controls (opt-out, data residency) — Railway serves this need; Arcade privacy hardening deferred to future version.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 60 tools are callable through the Arcade platform and return correct results matching their Railway counterparts.
- **SC-002**: Deployment to Arcade completes successfully via `arcade deploy` in under 10 minutes.
- **SC-003**: Existing Railway deployment (STDIO, Streamable HTTP, Worker modes) passes all 1020+ existing tests with zero regressions.
- **SC-004**: A developer unfamiliar with the project can deploy to either platform by following only the written documentation.
- **SC-005**: Adding a new tool requires changes in at most 2 additional files (Arcade wrapper + Arcade tool count test) beyond the existing process.
- **SC-006**: The `arcade-mcp` dependency is optional — running `uv sync` without `[arcade]` extra produces a working FastMCP server with no import errors.
- **SC-007**: PoC with 3-5 tools validates successfully on Arcade Hobby plan before full 60-tool migration proceeds.
