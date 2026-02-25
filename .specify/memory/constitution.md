<!--
Sync Impact Report
===================
Version change: 1.0.0 -> 1.1.0 (MINOR)
Modified principles:
  - Principle II: Modular Domain Architecture — expanded to include Czech
    healthcare submodule pattern under czech/ namespace
  - Principle III: Authoritative Data Sources — added Czech healthcare
    APIs (SUKL, MKN-10, NRPZS, SZV, VZP); added degradation policy for
    non-functional external APIs
Added sections:
  - Technical Constraints: internationalization (ensure_ascii=False)
Removed sections: None
Templates requiring updates:
  - .specify/templates/plan-template.md: ✅ compatible
  - .specify/templates/spec-template.md: ✅ compatible
  - .specify/templates/tasks-template.md: ✅ compatible
Follow-up TODOs:
  - Verify NRPZS, SZV/NZIP, VZP API status and decide retain/remove
-->

# BioMCP Constitution

## Core Principles

### I. MCP Protocol First

Every feature MUST be implemented as an MCP-compliant tool or resource.
The Model Context Protocol specification is the authoritative interface
contract. All tools MUST follow MCP input/output conventions and MUST be
registered through the MCP server. New functionality that cannot be
expressed as an MCP tool MUST be justified in writing before implementation.

**Rationale**: BioMCP exists to bridge AI assistants and biomedical data.
MCP compliance ensures interoperability with any MCP-compatible client
(Claude Desktop, agents, third-party integrations).

### II. Modular Domain Architecture

Each biomedical domain (articles, trials, variants, genes, diseases,
drugs, biomarkers, organizations, interventions, openfda) MUST be
implemented as an independent module under `src/biomcp/`. Czech
healthcare domains (sukl, mkn, nrpzs, szv, vzp) MUST be organized
under the `src/biomcp/czech/` namespace with tool registrations
centralized in `czech/czech_tools.py`. Modules MUST NOT import from
sibling domain modules directly. Shared functionality MUST live in
top-level utility modules (`http_client.py`, `cbioportal_helper.py`,
`exceptions.py`, etc.). New domains MUST follow the existing pattern:
`__init__.py` + domain-specific files (search, getter, fetch).

**Rationale**: Independent modules enable parallel development, isolated
testing, and clear ownership. Adding a new data source MUST NOT require
modifying existing domain modules. The `czech/` namespace groups
locale-specific modules while maintaining the same isolation guarantees.

### III. Authoritative Data Sources

BioMCP MUST integrate only with established, authoritative biomedical
and healthcare databases and APIs:

- **Global**: PubMed, ClinicalTrials.gov, NCI, MyVariant.info,
  MyGene.info, MyDisease.info, MyChem.info, cBioPortal, OncoKB,
  OpenFDA, TCGA/GDC, Ensembl
- **Czech healthcare**: SUKL (drug registry), MKN-10 (ICD-10 CZ),
  NRPZS (provider registry), SZV (procedure codes), VZP (insurance
  codebooks)

Every external API endpoint MUST be documented in
`THIRD_PARTY_ENDPOINTS.md`. Data returned to the user MUST be attributed
to its source. BioMCP MUST NOT fabricate, interpolate, or infer
biomedical data that is not present in the source response.

When an external API becomes non-functional (returns persistent 404 or
is retired), the affected tools MUST remain in the codebase with unit
tests (mocked) passing. The situation MUST be documented in CLAUDE.md
Known Issues. A decision to remove the tools MUST go through a PR with
maintainer approval.

**Rationale**: Biomedical data accuracy is safety-critical. Incorrect
variant annotations or trial eligibility data can have real-world
clinical consequences. Czech healthcare data enables local clinical
decision support for Czech-speaking users.

### IV. CLI & MCP Dual Access

Every search and fetch operation MUST be accessible via both the MCP
server (tools) and the CLI (`biomcp` command). The CLI module under
`src/biomcp/cli/` MUST mirror the MCP tool surface. Output MUST support
both JSON (machine-readable) and human-readable formats. CLI commands
MUST use stdout for data and stderr for errors/diagnostics.

**Rationale**: CLI access enables testing, debugging, scripting, and
use outside MCP contexts. Dual access ensures feature parity and
provides a validation layer for MCP tool behavior.

### V. Testing Rigor

All new features MUST include unit tests. Integration tests (tests that
call external APIs) MUST be marked with `@pytest.mark.integration` and
MUST be runnable independently of unit tests. Tests MUST NOT depend on
network availability for the unit test suite. Mocking external HTTP calls
is REQUIRED for unit tests. The test directory structure MUST mirror the
source structure under `tests/`. CI MUST pass all unit tests; integration
test failures MUST NOT block the build.

**Rationale**: BioMCP depends on numerous external APIs that are outside
our control. Separating unit and integration tests ensures fast,
reliable CI while still validating real API behavior in dedicated runs.

## Technical Constraints

- **Python**: 3.10+ (no lower bound negotiable)
- **Package manager**: `uv` (recommended), `pip` (supported)
- **HTTP client**: `httpx` with async support via centralized
  `http_client.py`
- **Data validation**: Pydantic v2 models for all API responses
- **MCP SDK**: `mcp[cli] >=1.12.3, <2.0.0`
- **Linting/Formatting**: `ruff` for linting and formatting
- **Type checking**: `mypy` for static type analysis
- **License**: MIT - all contributions MUST be MIT-compatible
- **Transport modes**: STDIO (default), SSE (legacy), Streamable HTTP
  (recommended for deployment)
- **External API tokens**: MUST be optional; core functionality MUST
  work without authentication (higher rate limits MAY require tokens)
- **Internationalization**: All JSON serialization MUST use
  `ensure_ascii=False` to preserve Czech diacritics and other non-ASCII
  characters

## Development Workflow

- **Branching**: Feature branches from `main`, merged via pull request
- **Code review**: All PRs MUST be reviewed before merge
- **Testing gate**: `make test` (unit tests) MUST pass before merge;
  integration tests run separately and are advisory
- **Commit style**: Conventional commits preferred
  (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`)
- **Documentation**: New MCP tools MUST be documented in `README.md`
  and relevant developer guides under `docs/`
- **Dependency management**: `pyproject.toml` is the single source of
  truth; use `uv` for dependency resolution
- **Pre-commit hooks**: `pre-commit` MUST be installed for local
  development (`ruff` checks enforced)

## Governance

This constitution is the authoritative reference for BioMCP development
decisions. It supersedes ad-hoc conventions and informal agreements.

**Amendment process**:
1. Propose the change in a PR modifying this file
2. Provide rationale and impact assessment
3. Obtain maintainer approval
4. Update version following semantic versioning (below)

**Versioning policy**:
- MAJOR: Principle removal or redefinition that changes project direction
- MINOR: New principle added or existing principle materially expanded
- PATCH: Clarifications, wording improvements, non-semantic changes

**Compliance review**:
- All PRs SHOULD be checked against applicable principles
- Violations MUST be documented and justified in PR description
- Complexity beyond the minimum required MUST be justified

**Version**: 1.1.0 | **Ratified**: 2026-02-17 | **Last Amended**: 2026-02-25
