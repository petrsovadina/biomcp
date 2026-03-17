# Research: Validace UI obsahu

**Branch**: `007-validate-ui-content` | **Date**: 2026-03-17

## Výsledek auditu

Kompletní audit obou UI (landing page + dokumentace) odhalil **10 konkrétních problémů**. Žádné NEEDS CLARIFICATION — všechny opravy jsou jednoznačné.

### R-001: Aktuální verze balíčku

**Decision**: v0.8.0
**Rationale**: pyproject.toml definuje `version = "0.8.0"`, landing page ukazuje zastaralé v0.7.3
**Alternatives**: Žádné — verze je jednoznačná

### R-002: Název hlavní branch

**Decision**: `main`
**Rationale**: Konsolidováno v 003-git-workflow. `python-main` již neexistuje.
**Alternatives**: Žádné

### R-003: Správný adresář po git clone

**Decision**: `cd CzechMedMCP` (název GitHub repozitáře)
**Rationale**: `git clone github.com/petrsovadina/CzechMedMCP` vytvoří adresář `CzechMedMCP`
**Alternatives**: `cd biomcp` — zastaralé, neodpovídá názvu repozitáře

### R-004: Transport mode CLI flag

**Decision**: `--mode streamable_http` (produkce), `--mode worker` (legacy SSE)
**Rationale**: CLI implementace v `cli/server.py` používá `--mode`, ne `--transport`
**Alternatives**: Žádné

### R-005: Názvy výjimek

**Decision**: `CzechMedMCPError` (base), `CzechMedMCPSearchError`, `InvalidDomainError`, `InvalidParameterError`, `SearchExecutionError`, `ResultParsingError`
**Rationale**: Přejmenováno z `BioMCPError` v rámci rename (002-codebase-stabilization)
**Alternatives**: Žádné

### R-006: PyPI dostupnost

**Decision**: Balíček NENÍ na PyPI. Primární instalace: `uv tool install git+https://github.com/petrsovadina/CzechMedMCP.git`
**Rationale**: Upstream biomcp-python (v0.7.3) na PyPI existuje, ale fork czechmedmcp nikdy nebyl publikován
**Alternatives**: Publikace na PyPI — budoucí práce, mimo scope
