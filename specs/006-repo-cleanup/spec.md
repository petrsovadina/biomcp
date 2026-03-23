# Feature Specification: Repository Cleanup

**Feature Branch**: `006-repo-cleanup`
**Created**: 2026-03-16
**Status**: Completed
**Input**: Důkladná analýza projektu, identifikace a odstranění mrtvého kódu, nepoužívaných závislostí a nepotřebných souborů pro pročištění celého repozitáře.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Odstranění mrtvého kódu (Priority: P1)

Jako maintainer chci odstranit zdrojové soubory, které nejsou nikde importovány ani používány, aby repozitář obsahoval pouze aktivní kód a noví přispěvatelé nebyli zmateni mrtvým kódem.

**Why this priority**: Mrtvý kód vytváří falešné závislosti, zvyšuje dobu onboardingu a komplikuje refaktoring. Každý nepoužívaný soubor je potenciální zdroj mylných předpokladů.

**Independent Test**: Po odstranění souborů všechny testy projdou (`pytest -m "not integration"`), lint projde (`ruff check`), MCP server se spustí a zaregistruje správný počet nástrojů.

**Acceptance Scenarios**:

1. **Given** repozitář obsahuje soubor `request_batcher.py`, který není nikde importován, **When** maintainer provede cleanup, **Then** soubor je odstraněn a testy projdou
2. **Given** repozitář obsahuje soubor `articles/search_optimized.py`, který není nikde importován, **When** maintainer provede cleanup, **Then** soubor je odstraněn a testy projdou
3. **Given** repozitář obsahuje permanentně nefunkční test `test_pydantic_ai_integration.py` (xfail), **When** maintainer provede cleanup, **Then** test soubor je odstraněn
4. **Given** kód závisí na `pydantic-ai` pouze kvůli odstraněnému testu, **When** test je odstraněn, **Then** závislost `pydantic-ai` je také odstraněna z pyproject.toml

---

### User Story 2 — Pročištění závislostí (Priority: P1)

Jako maintainer chci odstranit nepoužívané závislosti z pyproject.toml, aby instalace projektu byla rychlejší a neobsahovala zbytečné balíčky.

**Why this priority**: Nepoužívané závislosti zpomalují instalaci, zvětšují Docker image a mohou být bezpečnostní riziko. mkdocs infrastruktura je zcela nahrazena Nextra.

**Independent Test**: `uv sync --group dev` proběhne úspěšně. `deptry` nereportuje žádné nepoužité závislosti. Všechny testy projdou.

**Acceptance Scenarios**:

1. **Given** pyproject.toml obsahuje mkdocs závislosti, které projekt nepoužívá (Nextra je náhrada), **When** maintainer provede cleanup, **Then** `mkdocs`, `mkdocs-material` a `mkdocstrings[python]` jsou odstraněny z dev závislostí
2. **Given** pyproject.toml obsahuje `PyYAML` (komentář říká "mkdocs.yml parsing"), **When** mkdocs je odstraněn, **Then** `PyYAML` je také odstraněn
3. **Given** pyproject.toml obsahuje `tomlkit`, které není nikde importováno, **When** maintainer provede cleanup, **Then** `tomlkit` je odstraněn
4. **Given** pyproject.toml obsahuje `pydantic-ai` pro testovací integraci, **When** test soubor je odstraněn (US1), **Then** `pydantic-ai` je také odstraněn

---

### User Story 3 — Aktualizace dokumentace a validace (Priority: P2)

Jako maintainer chci, aby CLAUDE.md a README odrážely provedené změny, a aby celý projekt prošel kompletní kontrolou kvality po cleanup.

**Why this priority**: Dokumentace musí být v souladu s realitou. Po odstranění souborů a závislostí je potřeba ověřit konzistenci.

**Independent Test**: `make check` projde. CLAUDE.md neobsahuje zmínky o odstraněných souborech. MCP integration test ověří správný počet nástrojů (60).

**Acceptance Scenarios**:

1. **Given** CLAUDE.md zmiňuje `test_pydantic_ai_integration.py` v Známých problémech, **When** test je odstraněn, **Then** zmínka je odstraněna z CLAUDE.md
2. **Given** čistý kód po cleanup, **When** se spustí `make check`, **Then** ruff, mypy, pre-commit a deptry projdou bez chyb
3. **Given** MCP server má registrovat přesně 60 nástrojů, **When** se spustí integration test, **Then** počet nástrojů je stále 60

---

### Edge Cases

- Co když `request_batcher.py` je importován podmíněně? Ověřit grep na celém src/ a tests/
- Co když odstranění `pydantic-ai` rozbije jiný test? Prohledat všechny testy na import pydantic_ai
- Co když `http_client_simple.py` je používán jako fallback za runtime podmínek? Nechat ho, pokud je importován

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Soubor `src/czechmedmcp/request_batcher.py` MUSÍ být odstraněn (nulové importy)
- **FR-002**: Soubor `src/czechmedmcp/articles/search_optimized.py` MUSÍ být odstraněn (nulové importy)
- **FR-003**: Soubor `tests/test_pydantic_ai_integration.py` MUSÍ být odstraněn (permanentně xfail)
- **FR-004**: Dev závislosti `mkdocs`, `mkdocs-material`, `mkdocstrings[python]` MUSÍ být odstraněny z pyproject.toml
- **FR-005**: Dev závislost `PyYAML` MUSÍ být odstraněna z pyproject.toml (používána pouze pro mkdocs)
- **FR-006**: Dev závislost `tomlkit` MUSÍ být odstraněna z pyproject.toml (nulové importy)
- **FR-007**: Dev závislost `pydantic-ai` MUSÍ být odstraněna z pyproject.toml (jediný uživatel je odstraněný test)
- **FR-008**: Všechny existující testy MUSÍ projít po cleanup (`pytest -m "not integration"`)
- **FR-009**: Lint a typová kontrola MUSÍ projít (`ruff check`, `mypy`)
- **FR-010**: MCP server MUSÍ zaregistrovat přesně 60 nástrojů po cleanup
- **FR-011**: CLAUDE.md MUSÍ být aktualizován (odstraněny zmínky o smazaných souborech)
- **FR-012**: `http_client_simple.py` NESMÍ být odstraněn (je importován jako fallback v `http_client.py`)

### Assumptions

- Počet MCP nástrojů (60) se nemění — odstraňujeme pouze mrtvý kód, ne funkční nástroje
- `http_client_simple.py` zůstává — je aktivně importován jako fallback
- Prázdné `__init__.py` v subpackages zůstávají — jsou standardní Python package markers
- Specs v `specs/` zůstávají — slouží jako historická dokumentace rozhodnutí
- `example_scripts/` zůstávají — jsou reference pro uživatele

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Počet odstraněných zdrojových souborů je přesně 3 (request_batcher.py, search_optimized.py, test_pydantic_ai_integration.py)
- **SC-002**: Počet odstraněných dev závislostí je přesně 6 (mkdocs, mkdocs-material, mkdocstrings, PyYAML, tomlkit, pydantic-ai)
- **SC-003**: Všechny testy projdou po cleanup (0 failures)
- **SC-004**: MCP server registruje přesně 60 nástrojů
- **SC-005**: `make check` projde bez chyb (ruff, mypy, pre-commit, deptry)
- **SC-006**: Instalace projektu (`uv sync --group dev`) proběhne úspěšně
