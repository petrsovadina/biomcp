# Implementation Plan: Validace UI obsahu

**Branch**: `007-validate-ui-content` | **Date**: 2026-03-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/007-validate-ui-content/spec.md`

## Summary

Oprava zavádějících a zastaralých textů v landing page (apps/web) a dokumentaci (apps/docs). Čistě editační práce — žádný nový kód, žádné nové závislosti. Identifikováno 10 konkrétních problémů z kompletního auditu obou UI.

## Technical Context

**Language/Version**: TypeScript/MDX (Next.js 15, Nextra 4)
**Primary Dependencies**: Next.js, Nextra, React
**Storage**: N/A
**Testing**: grep validace (nulové výskyty zastaralých referencí)
**Target Platform**: Vercel (web + docs)
**Project Type**: Content fix (documentation and landing page text edits)
**Performance Goals**: N/A
**Constraints**: Žádné nové závislosti, žádné strukturální změny
**Scale/Scope**: ~15 souborů, ~30 řádků změn

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Relevance | Status |
|-----------|-----------|--------|
| I. MCP Protocol First | N/A — žádné nové nástroje | PASS |
| II. Modular Domain Architecture | N/A — editace pouze v apps/ | PASS |
| III. Authoritative Data Sources | ALIGNS — opravujeme nepřesné reference na zdroje | PASS |
| IV. CLI & MCP Dual Access | N/A | PASS |
| V. Testing Rigor | ALIGNS — validace grepem na zastaralé reference | PASS |
| Development Workflow | ALIGNS — feature branch, conventional commits | PASS |

**Gate Result**: PASS — čistě dokumentační oprava, žádné porušení.

## Project Structure

### Files to EDIT

**Landing page (apps/web/):**

```text
apps/web/src/components/hero.tsx          # FR-006: verze v0.7.3 → v0.8.0
```

**Dokumentace (apps/docs/):**

```text
# FR-001, FR-002, FR-008: Branch a adresář reference
apps/docs/app/vyvojari/page.mdx               # python-main → main, cd biomcp → cd CzechMedMCP
apps/docs/app/vyvojari/lokalni-vyvoj/page.mdx  # python-main → main, cd biomcp → cd CzechMedMCP, docs-site → apps/docs
apps/docs/app/zaciname/instalace/page.mdx      # cd biomcp → cd CzechMedMCP, python-main → main

# FR-004: Transport mode flag
apps/docs/app/reference/konfigurace/page.mdx   # --transport sse → --mode streamable_http/worker

# FR-005: Exception hierarchy names
apps/docs/app/architektura/vyjimky/page.mdx    # BioMCPError → CzechMedMCPError

# FR-007: Instalační instrukce
apps/docs/app/zaciname/instalace/page.mdx      # pip install upozornění
apps/docs/app/reference/page.mdx               # pip install upozornění

# FR-010: Deployment adresáře
apps/docs/app/vyvojari/deployment/page.mdx     # docs-site → apps/docs
```

### Files NOT changed

```text
apps/web/src/components/features.tsx     # Čísla OK (60, 23, 37)
apps/web/src/components/tool-catalog.tsx # Nástroje OK
apps/web/src/components/testimonial.tsx  # Statistiky OK
apps/docs/app/nastroje/page.mdx         # Katalog OK
apps/docs/app/prirucka/**               # Příručky OK
```

## Implementation Phases

### Phase 1: Oprava zastaralých referencí (US1 — P1)

Soubory: 4 MDX stránky v docs

| Soubor | Změna |
|--------|-------|
| `vyvojari/page.mdx` | `python-main` → `main`, `cd biomcp` → `cd CzechMedMCP` |
| `vyvojari/lokalni-vyvoj/page.mdx` | `python-main` → `main`, `cd biomcp` → `cd CzechMedMCP`, `docs-site/` → `apps/docs/`, `biomcp/` → `czechmedmcp/` v adresářové struktuře |
| `zaciname/instalace/page.mdx` | `cd biomcp` → `cd CzechMedMCP`, `python-main` → `main` |
| `vyvojari/deployment/page.mdx` | `docs-site` → `apps/docs` (2x) |

### Phase 2: Oprava nesprávných příkazů a názvů (US2 — P1)

| Soubor | Změna |
|--------|-------|
| `reference/konfigurace/page.mdx` | `--transport sse` → `--mode streamable_http` |
| `architektura/vyjimky/page.mdx` | `BioMCPError` → `CzechMedMCPError`, `BioMCPSearchError` → `CzechMedMCPSearchError` atd. |
| `apps/web/.../hero.tsx` | `v0.7.3` → `v0.8.0` |

### Phase 3: Oprava instalačních instrukcí (US3 — P2)

| Soubor | Změna |
|--------|-------|
| `zaciname/instalace/page.mdx` | Přidat upozornění o PyPI, preferovat `uv tool install` nebo git clone |
| `reference/page.mdx` | Aktualizovat quick reference instalační příkaz |

### Phase 4: Validace (US4 — P3)

1. Grep na `python-main` v `apps/` → 0 výsledků
2. Grep na `cd biomcp` v `apps/` → 0 výsledků
3. Grep na `BioMCPError` v `apps/` → 0 výsledků
4. Grep na `--transport sse` v `apps/` → 0 výsledků
5. Grep na `docs-site` v `apps/` → 0 výsledků
6. Ověřit verzi na landing page = verze v pyproject.toml

## Build Sequence

```text
Phase 1 (branch/directory refs)
    ↓
Phase 2 (commands/names)     ← depends on Phase 1 for zaciname/instalace overlap
    ↓
Phase 3 (installation docs)  ← depends on Phase 2 for same-file edits
    ↓
Phase 4 (validation)         ← depends on all previous phases
```

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Přehlédnutí dalšího zastaralého výskytu | Low | Low | Grep validace v Phase 4 |
| Rozbití MDX syntaxe při editaci | Medium | Low | Lokální build test (npm run build:docs) |
| Verze se změní znovu | Low | Medium | Edge case: budoucí automatizace |
