# Specification: 001-czechmedmcp-implementation

## Status

| Field | Value |
|-------|-------|
| **Created** | 2026-03-01 |
| **Current Phase** | Research → PRD |
| **Last Updated** | 2026-03-01 |

## Documents

| Document | Status | Notes |
|----------|--------|-------|
| product-requirements.md | pending | — |
| solution-design.md | pending | — |
| implementation-plan.md | pending | — |

**Status values**: `pending` | `in_progress` | `completed` | `skipped`

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-01 | Restart specifikace dle speckit metodiky | Předchozí analýza (gap-analysis, roadmap) nebyla vytvořena dle předepsaného PRD→SDD→PLAN workflow |
| 2026-03-01 | Scaffold spec 001-czechmedmcp-implementation | Čistý start s plným specify workflow |
| 2026-03-01 | Start od PRD fáze | Doporučený postup — definovat CO a PROČ před technickým návrhem |
| 2026-03-01 | Team Mode pro research | Komplexní doména (5 modulů, 8 datových zdrojů, zdravotnictví) vyžaduje důkladný multi-perspektivní výzkum |

## Context

**Cíl:** CzechMedMCP — rozšíření BioMCP forku o kompletní české zdravotnické moduly (SUKL, MKN-10, NRPZS, SZV, VZP) se 23 českými nástroji, 3 workflow orchestracemi. Cílový stav: MCP server s 63 nástroji pro české lékaře v platformě Medevio.

**Aktuální stav:** CzechMedMCP v0.7.3 na branch `python-main`, 60 nástrojů (23 českých + 37 globálních). Všech 5 českých modulů funkčních, 3 workflow orchestrace, dokumentace aktualizována.

**Constitution:** `.specify/memory/constitution.md` v1.1.0 — MCP Protocol First, Modular Domain Architecture, Authoritative Data Sources.

---
*This file is managed by the specify-meta skill.*
