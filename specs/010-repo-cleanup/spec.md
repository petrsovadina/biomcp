# Feature Specification: Systematické pročištění repozitáře

**Feature Branch**: `010-repo-cleanup`
**Created**: 2026-03-22
**Status**: Draft
**Input**: User description: "Systematické pročištění repozitáře: odstranění duplicitních, legacy, dočasných a zavádějících souborů; aktualizace nepravdivých informací; sjednocení struktury pro přehlednost dalších vývojářů"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Odstranění duplicitních souborů ze specs/ (Priority: P1)

Jako vývojář chci, aby adresář `specs/` obsahoval pouze kanonické verze specifikačních souborů bez duplicitních kopií (soubory s příponou " 2", " 3"), které vznikly nechtěným kopírováním.

**Why this priority**: Duplicitní soubory jsou nejviditelnějším problémem — matou vývojáře, zvětšují repo a vytvářejí riziko editace nesprávné kopie.

**Independent Test**: Po odstranění spočítat soubory v `specs/` — žádný soubor ani adresář nesmí obsahovat " 2" nebo " 3" v názvu.

**Acceptance Scenarios**:

1. **Given** specs/ obsahuje duplicáty jako `plan 2.md`, `spec 3.md`, `checklists 2/`, **When** spustím `find specs/ -name "* [23]*"`, **Then** výsledek je prázdný.
2. **Given** kanonické verze (`plan.md`, `spec.md`) existují, **When** porovnám obsah s duplicátem, **Then** jsou identické (duplikát nemá unikátní obsah).
3. **Given** duplicáty jsou odstraněny, **When** spustím testy, **Then** všech 1020+ testů projde beze změn.

---

### User Story 2 - Odstranění obrázků a dočasných souborů z kořene repozitáře (Priority: P1)

Jako vývojář chci, aby kořenový adresář obsahoval pouze standardní projektové soubory (README, pyproject.toml, Dockerfile atd.) bez screenshotů, duplicitních konfigurací a build artefaktů.

**Why this priority**: 17 screenshotů (~2.4 MB) a duplicitní `.dockerignore 3/4` znečišťují kořenový adresář a zpomalují git operace.

**Independent Test**: Po čištění spočítat soubory v kořeni — žádné `.jpeg`, `.png`, `.dockerignore N` soubory. `ls *.jpeg *.png` vrátí prázdný výsledek.

**Acceptance Scenarios**:

1. **Given** kořen obsahuje 17 screenshotů (dark-*.jpeg, light-*.png), **When** je odstraním, **Then** `ls *.jpeg *.png 2>/dev/null` v kořeni vrátí prázdný výsledek.
2. **Given** existují `.dockerignore 3` a `.dockerignore 4`, **When** je odstraním, **Then** zůstane pouze `.dockerignore` (originál).
3. **Given** existuje duplicitní `Caddyfile 3`, **When** je odstraním, **Then** zůstane pouze `Caddyfile`.
4. **Given** kořen obsahuje `build/` adresář, **When** jej odstraním a přidám do .gitignore, **Then** `git status` nehlásí build/ jako untracked.

---

### User Story 3 - Oprava nepravdivých a zastaralých informací (Priority: P1)

Jako vývojář chci, aby všechny URL, verze a tvrzení v dokumentaci a konfiguraci odpovídaly skutečnému stavu projektu.

**Why this priority**: Nepravdivé informace vedou vývojáře na špatné adresy a vytvářejí nedůvěru v dokumentaci.

**Independent Test**: Ověřit každou opravenou URL/tvrzení manuálně nebo automatizovaným curl testem.

**Acceptance Scenarios**:

1. **Given** `pyproject.toml` obsahuje `Documentation = "https://petrsovadina.github.io/biomcp/"` (stará URL), **When** opravím na aktuální docs URL, **Then** URL je validní a odpovídá skutečným docs.
2. **Given** `.env.example` používá prefix `BIOMCP_*` pro proměnné, **When** přejmenuji na `CZECHMEDMCP_*`, **Then** prefix odpovídá názvu balíčku.
3. **Given** kořenový `vercel.json` obsahuje nesprávné cesty (`web/.next`), **When** je odstraním nebo opravím, **Then** Vercel deployment funguje z app-level konfigurací.

---

### User Story 4 - Archivace dokončených specifikací (Priority: P2)

Jako vývojář chci jasně vidět, které specifikace jsou aktivní a které jsou dokončené, aby se nový vývojář snadno zorientoval.

**Why this priority**: 9 spec adresářů bez jasného rozlišení stavu stěžují orientaci.

**Independent Test**: Každý spec adresář má jasný status indikátor a dokončené specs jsou vizuálně odlišené.

**Acceptance Scenarios**:

1. **Given** specs 001-003 jsou merged, **When** se podívám na `specs/` adresář, **Then** je jasné které jsou aktivní a které dokončené.
2. **Given** spec 000 má 79/83 tasků hotových, **When** se podívám na jeho status, **Then** je jasné že je rozpracovaný.

---

### User Story 5 - Aktualizace .gitignore pro prevenci budoucích problémů (Priority: P2)

Jako vývojář chci, aby .gitignore obsahoval pravidla pro všechny typy souborů, které by neměly být v gitu, aby se problémy z US1 a US2 nemohly opakovat.

**Why this priority**: Preventivní opatření -- bez aktualizace .gitignore se budou duplicáty a build artefakty objevovat znovu.

**Independent Test**: `git check-ignore` pro typické problematické soubory vrátí pozitivní výsledek.

**Acceptance Scenarios**:

1. **Given** .gitignore je aktualizován, **When** vytvořím soubor `test 2.md` v specs/, **Then** `git check-ignore "specs/test 2.md"` potvrdí ignorování.
2. **Given** .gitignore obsahuje `build/`, **When** vytvořím build artefakty, **Then** nejsou trackované gitem.
3. **Given** .gitignore obsahuje pattern pro screenshoty v kořeni, **When** přidám screenshot, **Then** git jej ignoruje.

---

### Edge Cases

- Co když některý duplicitní soubor obsahuje unikátní změny? Porovnat obsah před smazáním; pokud se liší, zachovat obsah do kanonické verze.
- Co když `.env.example` přejmenování `BIOMCP_*` na `CZECHMEDMCP_*` rozbije existující deploymenty? Přidat komentář o zpětné kompatibilitě.
- Co když odstranění kořenového `vercel.json` rozbije Vercel deploy? Ověřit, že app-level configs v `apps/web/` a `apps/docs/` jsou dostatečné.
- Co když git history obsahuje velké binární soubory (screenshoty)? Git filter-branch je out of scope -- pouze odstraníme soubory z HEAD, historie zůstane.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST NOT contain duplicate files in `specs/` (files with " 2" or " 3" suffixes).
- **FR-002**: Root directory MUST NOT contain screenshot images (.jpeg, .png) from feature development.
- **FR-003**: Root directory MUST NOT contain duplicate configuration files (`.dockerignore 3`, `.dockerignore 4`, `Caddyfile 3`).
- **FR-004**: `pyproject.toml` documentation URL MUST point to the actual deployed documentation site.
- **FR-005**: Environment variable naming in `.env.example` MUST use `CZECHMEDMCP_*` prefix consistent with the package name.
- **FR-006**: Root `vercel.json` MUST either be removed or contain correct paths for current monorepo structure.
- **FR-007**: `build/` directory MUST be in `.gitignore` and removed from tracking.
- **FR-008**: `.gitignore` MUST include patterns preventing future duplicate file commits (macOS file copy patterns).
- **FR-009**: All existing tests (1020+) MUST pass after cleanup with zero regressions.
- **FR-010**: Completed spec directories MUST have clear status indicators (e.g., status field in spec.md updated to "Completed" or "Merged").

### Key Entities

- **Duplicate files**: Files ending with " 2", " 3" suffixes -- macOS Finder copy artifacts.
- **Root clutter**: Screenshots, duplicate configs, build artifacts in repository root.
- **Stale information**: Incorrect URLs, outdated naming conventions, conflicting configs.

## Assumptions

- Duplicate files (suffix " 2", " 3") are exact copies of originals with no unique content worth preserving.
- Existing Vercel deployments use app-level `vercel.json` configs, not the root-level one.
- Renaming `BIOMCP_*` environment variables does not affect production Railway deployment (Railway uses `MCP_MODE` and `PORT`, not `BIOMCP_*`).
- Git history cleanup (BFG, filter-branch) for removing large files from history is out of scope.
- Completed specs are historical records worth keeping, but should be clearly marked as done.

## Out of Scope

- Git history rewriting (filter-branch, BFG) for removing large files from history.
- Refactoring source code structure or renaming modules.
- Changing deployment configurations beyond fixing incorrect information.
- Adding new features or functionality.
- Updating test content or adding new tests (beyond ensuring existing tests pass).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero files with " 2" or " 3" suffixes exist anywhere in the repository.
- **SC-002**: Root directory contains fewer than 25 files (currently ~40+ with screenshots and duplicates).
- **SC-003**: All URLs in `pyproject.toml` and documentation point to valid, accessible endpoints.
- **SC-004**: All existing 1020+ tests pass with zero regressions after cleanup.
- **SC-005**: A new developer can identify the purpose of every file in the root directory within 30 seconds per file.
- **SC-006**: `.gitignore` blocks at least 5 new categories of files (build/, screenshots, macOS copy duplicates, .next/, temp files).
- **SC-007**: Repository size reduction of at least 2 MB (from removed binary screenshots).
