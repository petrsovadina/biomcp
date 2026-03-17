# Feature Specification: Validace UI obsahu

**Feature Branch**: `007-validate-ui-content`
**Created**: 2026-03-17
**Status**: Draft
**Input**: Důkladná analýza a validace všech informací v uživatelském rozhraní, aby neobsahovaly zavádějící nebo mystifikující texty a tvrzení.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Oprava zastaralých referencí na branch a adresáře (Priority: P1)

Jako vývojář chci, aby dokumentace obsahovala správné názvy branchí a adresářů, protože podle zastaralých instrukcí (`python-main`, `cd biomcp`, `docs-site/`) se mi nepodaří projekt naklonovat a nastavit.

**Why this priority**: Zastaralé reference přímo blokují nové přispěvatele — příkazy selžou a vývojář uvízne hned na začátku.

**Independent Test**: Po opravě všech referencí může nový vývojář projít celou Getting Started sekci bez jediné chyby.

**Acceptance Scenarios**:

1. **Given** dokumentace obsahuje `git checkout python-main`, **When** maintainer provede opravu, **Then** všechny výskyty jsou nahrazeny `git checkout main`
2. **Given** dokumentace obsahuje `cd biomcp`, **When** maintainer provede opravu, **Then** všechny výskyty jsou nahrazeny `cd CzechMedMCP`
3. **Given** dokumentace obsahuje `docs-site/`, **When** maintainer provede opravu, **Then** všechny výskyty jsou nahrazeny `apps/docs/`
4. **Given** developer overview uvádí `Branch: python-main (aktivní vývoj)`, **When** maintainer provede opravu, **Then** text uvádí `Branch: main`

---

### User Story 2 — Oprava nesprávných příkazů a názvů (Priority: P1)

Jako uživatel chci, aby dokumentované příkazy odpovídaly skutečnému CLI rozhraní, protože nesprávné příkazy vedou k frustraci a ztrátě důvěry v projekt.

**Why this priority**: Nesprávné příkazy přímo brání používání produktu a podkopávají důvěryhodnost dokumentace.

**Independent Test**: Každý dokumentovaný příkaz může být spuštěn bez chyby na čerstvé instalaci.

**Acceptance Scenarios**:

1. **Given** konfigurace uvádí `--transport sse`, **When** maintainer provede opravu, **Then** text uvádí `--mode streamable_http` nebo `--mode worker` podle kontextu
2. **Given** architektura výjimek dokumentuje `BioMCPError`, **When** maintainer provede opravu, **Then** všechny výskyty používají `CzechMedMCPError` a odpovídající podtřídy (`CzechMedMCPSearchError` atd.)
3. **Given** landing page terminal demo ukazuje `v0.7.3`, **When** maintainer provede opravu, **Then** verze odpovídá aktuální verzi v pyproject.toml (v0.8.0)

---

### User Story 3 — Oprava instalačních instrukcí (Priority: P2)

Jako nový uživatel chci, aby instalační instrukce odpovídaly realitě, protože pokus o instalaci přes `pip install czechmedmcp` selže, když balíček není na PyPI.

**Why this priority**: Prvotní zkušenost s produktem je klíčová — nefunkční instalace odradí většinu potenciálních uživatelů.

**Independent Test**: Uživatel může nainstalovat projekt podle dokumentace na čerstvém systému s Python 3.10+.

**Acceptance Scenarios**:

1. **Given** instalační stránka nabízí `pip install czechmedmcp` jako primární metodu, **When** maintainer provede opravu, **Then** primární metodou je instalace z Git repozitáře a `pip` varianta je označena jako „dostupná po publikaci na PyPI" nebo odstraněna
2. **Given** quick reference uvádí `pip install czechmedmcp`, **When** maintainer provede opravu, **Then** instrukce odpovídá dostupným instalačním metodám

---

### User Story 4 — Ověření konzistence čísel a tvrzení (Priority: P3)

Jako návštěvník webu chci, aby všechna uváděná čísla a tvrzení odpovídala realitě, protože nepřesné statistiky podkopávají důvěryhodnost celého projektu.

**Why this priority**: Konzistence čísel posiluje důvěru, ale stávající čísla jsou z velké části správná — jde o prevenci budoucích nesrovnalostí.

**Independent Test**: Automatizovaný test ověří, že počet nástrojů na webu, v dokumentaci a v kódu je shodný.

**Acceptance Scenarios**:

1. **Given** web i dokumentace uvádějí 60 nástrojů, **When** se spustí regresní test, **Then** počet registrovaných nástrojů v kódu odpovídá číslu uváděnému v UI
2. **Given** web uvádí 23 českých a 37 globálních nástrojů, **When** se spustí validace, **Then** součet odpovídá 60 a rozdělení odpovídá skutečnosti

---

### Edge Cases

- Co když se verze v pyproject.toml změní znovu? Zvážit centralizaci verze pro landing page
- Co když se přidá nový nástroj? Počty na webu a v docs musí být aktualizovány současně s kódem
- Co když se balíček publikuje na PyPI v budoucnu? pip instrukce bude třeba obnovit

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Dokumentace NESMÍ obsahovat reference na branch `python-main` — všechny MUSÍ být nahrazeny `main`
- **FR-002**: Dokumentace NESMÍ obsahovat `cd biomcp` — všechny MUSÍ být nahrazeny `cd CzechMedMCP`
- **FR-003**: Dokumentace NESMÍ obsahovat `docs-site/` jako adresář — MUSÍ být nahrazen `apps/docs/`
- **FR-004**: Konfigurace NESMÍ dokumentovat `--transport sse` — MUSÍ uvádět `--mode streamable_http` nebo `--mode worker`
- **FR-005**: Architektura výjimek MUSÍ používat `CzechMedMCPError` místo `BioMCPError`
- **FR-006**: Landing page terminal demo MUSÍ zobrazovat aktuální verzi (v0.8.0, ne v0.7.3)
- **FR-007**: Instalační instrukce MUSÍ odpovídat dostupným metodám (git clone / uv, ne `pip install` pokud balíček není na PyPI)
- **FR-008**: Developer overview MUSÍ uvádět `main` jako hlavní branch
- **FR-009**: Adresářová struktura v lokálním vývoji MUSÍ odpovídat skutečnosti (`apps/docs/` místo `docs-site/`, `czechmedmcp/` místo `biomcp/`)
- **FR-010**: Vercel deployment sekce MUSÍ referencovat správné adresáře (`apps/docs` místo `docs-site`)

### Assumptions

- Počet MCP nástrojů (60) se nemění — opravujeme pouze nesprávné reference, ne funkčnost
- Balíček `czechmedmcp` aktuálně není na PyPI — instalace probíhá z Git repozitáře
- Hlavní branch je `main` (konsolidováno v 003-git-workflow)
- Všechna uváděná čísla (60 nástrojů, 23 českých, 37 globálních, 30M+ článků, 400K+ studií) jsou ověřena jako správná
- Landing page content je z 95% správný — problémy jsou lokalizované

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Nulový počet referencí na `python-main` branch v celém `apps/` adresáři
- **SC-002**: Nulový počet referencí na `cd biomcp` v celém `apps/` adresáři
- **SC-003**: Nulový počet referencí na `BioMCPError` v celém `apps/` adresáři
- **SC-004**: Nulový počet referencí na `--transport sse` v celém `apps/` adresáři
- **SC-005**: Verze zobrazená na landing page odpovídá verzi v pyproject.toml
- **SC-006**: Nový vývojář může projít Getting Started sekci bez chyby způsobené nesprávnou dokumentací
- **SC-007**: Všechna čísla nástrojů (60, 23, 37) na webu a v docs jsou konzistentní a odpovídají skutečnosti
