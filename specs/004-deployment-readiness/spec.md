# Feature Specification: Deployment Readiness Validace

**Feature Branch**: `004-deployment-readiness`
**Created**: 2026-03-16
**Status**: Completed
**Input**: Analýza a validace připravenosti projektu na nasazení — landing page, dokumentace, MCP server s nástroji.

## Audit Summary

Provedený audit odhalil, že projekt je **deployment-ready** s 2 minor issues:
- Dokumentace obsahuje zastaralé `biomcp-python` reference v CLI příkladech
- Stav: MCP server ✅, Landing page ✅, Docs ✅, Docker ✅, CI ✅, Auth ✅

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Oprava zastaralých CLI příkladů v dokumentaci (Priority: P1)

Uživatel, který čte dokumentaci a chce nastavit CzechMedMCP v Claude Desktop, najde příklady s `biomcp-python` a `biomcp run`, které neodpovídají aktuálnímu názvu balíčku `czechmedmcp`. To vede ke zmatku nebo chybě při instalaci.

**Why this priority**: Dokumentace je první kontakt nového uživatele. Chybné příklady znamenají, že uživatel nemůže produkt ani spustit.

**Independent Test**: Všechny `.mdx` soubory v `apps/docs/` obsahují výhradně `czechmedmcp` reference (žádné `biomcp-python` nebo `biomcp run`).

**Acceptance Scenarios**:

1. **Given** uživatel otevře dokumentaci na stránce „Začínáme", **When** zkopíruje Claude Desktop konfiguraci, **Then** konfigurace obsahuje `czechmedmcp` (ne `biomcp-python`)
2. **Given** uživatel hledá CLI příkaz v dokumentaci, **When** najde příklad, **Then** příkaz je `czechmedmcp run` (ne `biomcp run`)
3. **Given** uživatel chce nainstalovat balíček, **When** zkopíruje pip/uv příkaz, **Then** příkaz obsahuje `czechmedmcp`

---

### User Story 2 - Validace deployment konfigurace (Priority: P1)

Vývojář potřebuje ověřit, že všechny deployment konfigurace (Docker, Railway, Fly.io, Caddy) jsou konzistentní a obsahují správný název balíčku, správné porty a health check cesty.

**Why this priority**: Nekonzistentní konfigurace může způsobit selhání nasazení na produkci.

**Independent Test**: `grep -r "biomcp" Dockerfile* docker-compose* fly.toml railway.json Caddyfile` vrací 0 výsledků. Health endpoint vrací `{"status": "healthy"}`.

**Acceptance Scenarios**:

1. **Given** deployment config soubory existují, **When** se prohledají na `biomcp`, **Then** žádné výsledky (vše je `czechmedmcp`)
2. **Given** Dockerfile se buildí, **When** container startuje, **Then** health endpoint odpovídá na `/health`
3. **Given** CI pipeline je nakonfigurovaný, **When** se spustí na `main`, **Then** všech 5 jobů projde

---

### User Story 3 - Aktualizace landing page obsahu (Priority: P2)

Landing page v `apps/web/` musí odkazovat na správný název produktu CzechMedMCP a obsahovat aktuální informace o 60 nástrojích.

**Why this priority**: Landing page je veřejná prezentace produktu, ale není kritická pro technické nasazení.

**Independent Test**: Landing page se úspěšně buildí (`npm run build` v `apps/web/`) a neobsahuje zastaralé reference.

**Acceptance Scenarios**:

1. **Given** landing page zdrojový kód, **When** se hledá `biomcp` v textech, **Then** žádné výsledky kromě URL/GitHub odkazů na upstream repozitář
2. **Given** landing page, **When** se buildí, **Then** build proběhne bez chyb

---

### Edge Cases

- Co když upstream PyPI balíček `biomcp-python` stále existuje? → Zachovat zmínku v CHANGELOG jako historickou referenci, ale aktivní dokumentace musí odkazovat na `czechmedmcp`
- Co když docs build selže po úpravách? → Ověřit build lokálně před commitem
- Co když landing page komponenty importují zastaralé konstanty? → Prověřit imports v komponentách

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Dokumentace NESMÍ obsahovat `biomcp-python` jako název instalačního balíčku — MUSÍ být `czechmedmcp`
- **FR-002**: Dokumentace NESMÍ obsahovat `biomcp run` jako CLI příkaz — MUSÍ být `czechmedmcp run`
- **FR-003**: Claude Desktop konfigurace v dokumentaci MUSÍ používat aktuální název balíčku
- **FR-004**: Deployment konfigurace NESMÍ obsahovat zastaralé `biomcp` reference (kromě upstream URL)
- **FR-005**: Docs site MUSÍ se úspěšně buildovat po úpravách
- **FR-006**: Landing page MUSÍ se úspěšně buildovat
- **FR-007**: CI pipeline MUSÍ targetovat `main` branch a validovat 60 nástrojů

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 0 výskytů `biomcp-python` v aktivní dokumentaci (apps/docs/)
- **SC-002**: 0 výskytů `biomcp run` v aktivní dokumentaci (apps/docs/)
- **SC-003**: 0 výskytů `biomcp` v deployment konfiguracích (kromě upstream/historical references)
- **SC-004**: Docs build (`npm run build` v apps/docs/) proběhne bez chyb
- **SC-005**: Landing page build (`npm run build` v apps/web/) proběhne bez chyb
- **SC-006**: Všechny testy projdou (1020+ passed, 0 failed)

## Assumptions

- PyPI release `czechmedmcp` ještě neexistuje — uživatelé instalují z source/GitHub
- Landing page a docs se servírují přes Caddy v Docker compose production setup
- Upstream GitHub URL `genomoncology/biomcp` se NEZMĚNIL a je OK ho zachovat jako historickou referenci
