# Feature Specification: Git Workflow Systematizace

**Feature Branch**: `003-git-workflow`
**Created**: 2026-03-16
**Status**: Complete
**Input**: Zjednodušení a systematizace git workflow projektu CzechMedMCP. Dvě hlavní branches (main a python-main), python-main 17 commitů ahead bez remote, origin/main zastaralý. Stale tracking. Cíl: jedna hlavní branch, čistý remote, definovaný branching model.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Konsolidace na jednu hlavní branch (Priority: P1)

Vývojář potřebuje, aby projekt měl jednu jasnou hlavní branch (`main`), která obsahuje veškerý aktuální kód. Aktuálně existují dvě branches (`main` a `python-main`), kde `python-main` je 17 commitů napřed a `origin/main` na GitHubu je zastaralý. Vývojář nemůže jednoduše pushovat ani vytvářet PR, protože tracking je rozbitý.

**Why this priority**: Bez vyřešení tohoto nelze spolehlivě pracovat s remote repozitářem, vytvářet PR, ani spouštět CI. Blokuje veškerý další vývoj.

**Independent Test**: Po dokončení `git log --oneline -5 main` ukazuje aktuální commity (včetně rename), `git push origin main` proběhne bez chyb, `origin/main` na GitHubu odpovídá lokálnímu stavu.

**Acceptance Scenarios**:

1. **Given** projekt má dvě branches (main, python-main), **When** vývojář provede konsolidaci, **Then** existuje pouze branch `main` s veškerým aktuálním kódem
2. **Given** `origin/main` je zastaralý, **When** vývojář pushne konsolidovaný `main`, **Then** `origin/main` na GitHubu odpovídá lokálnímu stavu
3. **Given** branch `python-main` existuje lokálně, **When** je konsolidace dokončena, **Then** `python-main` je smazaná (vše je v `main`)

---

### User Story 2 - Vyčištění stale tracking a remote references (Priority: P1)

Vývojář vidí v `git branch -vv` stale tracking na neexistující remote branches (`origin/python-main: gone`, stale refs na `claude/sub-pr-2`, `manus-like`). To mate a způsobuje zmatky při práci s gitem.

**Why this priority**: Stale tracking způsobuje matoucí výstupy git příkazů a může vést k chybám při push/pull.

**Independent Test**: `git branch -vv` ukazuje pouze `main` s platným tracking na `origin/main`, žádné `[gone]` reference.

**Acceptance Scenarios**:

1. **Given** existují stale tracking references, **When** vývojář provede cleanup, **Then** `git branch -vv` neukazuje žádné `[gone]` branches
2. **Given** existují nepoužívané lokální branches, **When** cleanup proběhne, **Then** zbývá pouze `main`

---

### User Story 3 - Definovaný branching model pro budoucí vývoj (Priority: P2)

Vývojář potřebuje jasný, dokumentovaný branching model, aby každý budoucí vývoj probíhal systematicky. Model musí definovat jak vytvářet feature branches, jak pojmenovávat branches dle speckit konvence (číslo-název), jak mergovat zpět do main, a jaký je PR workflow.

**Why this priority**: Bez definovaného modelu se zmatek opakuje. Dokumentace zajistí konzistenci i při práci v různých sessions.

**Independent Test**: CLAUDE.md obsahuje sekci "Git Workflow" s jasnými pravidly, nová feature branch vytvořená přes speckit skript má správné pojmenování a tracking.

**Acceptance Scenarios**:

1. **Given** vývojář chce začít novou feature, **When** použije speckit workflow, **Then** je vytvořena branch `NNN-feature-name` z `main` s remote tracking
2. **Given** feature je hotová, **When** vývojář chce mergovat, **Then** vytvoří PR do `main` přes `gh pr create`
3. **Given** PR je merged, **When** vývojář uklidí, **Then** lokální feature branch je smazána a `main` je aktuální

---

### User Story 4 - Aktualizace CI pipeline na nový branching model (Priority: P2)

CI workflow (`.github/workflows/ci.yml`) aktuálně targetuje `python-main` branch. Po konsolidaci musí targetovat `main`.

**Why this priority**: CI musí běžet na správné branch, jinak se nespustí při push/PR.

**Independent Test**: Push na `main` spustí CI pipeline, PR do `main` spustí CI checks.

**Acceptance Scenarios**:

1. **Given** CI workflow targetuje `python-main`, **When** workflow je aktualizován, **Then** trigger branches jsou `main` (push i PR)
2. **Given** feature branch existuje, **When** je vytvořen PR do `main`, **Then** CI checks se automaticky spustí

---

### Edge Cases

- Co když někdo má lokální `python-main` branch a pullne? → Branch na remote neexistuje, git zobrazí varování. Dokumentovat v CHANGELOG.
- Co když CI workflow selže na `main` po force-push? → Force-push změní historii, ale obsah zůstává stejný. CI by měl projít.
- Co když upstream (genomoncology/biomcp) přidá nové branches? → Upstream remote zůstává readonly, neovlivňuje náš workflow.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Projekt MUSÍ mít jedinou hlavní branch pojmenovanou `main`
- **FR-002**: `origin/main` na GitHubu MUSÍ odpovídat lokálnímu `main` po dokončení
- **FR-003**: Všechny stale tracking references MUSÍ být odstraněny
- **FR-004**: Branch `python-main` MUSÍ být smazána (lokálně i remote)
- **FR-005**: CI workflow MUSÍ targetovat `main` branch pro push i PR triggers
- **FR-006**: CLAUDE.md MUSÍ obsahovat dokumentaci git workflow s pravidly pro branches
- **FR-007**: Branching model MUSÍ používat konvenci `NNN-feature-name` (speckit)
- **FR-008**: Feature branches MUSÍ být vytvářeny z aktuálního `main`
- **FR-009**: Merge do `main` MUSÍ probíhat přes PR (ne přímý push pro feature work)
- **FR-010**: Po merge feature branch MUSÍ být smazána (lokálně i remote)

### Key Entities

- **Main Branch (`main`)**: Jediná dlouhodobá branch, vždy deployable, chráněná PR workflow
- **Feature Branch (`NNN-name`)**: Krátkodobá branch pro konkrétní specifikaci, vytvořená přes speckit, mergovaná přes PR
- **Remote (`origin`)**: GitHub repozitář petrsovadina/biomcp
- **Upstream (`upstream`)**: Readonly reference na genomoncology/biomcp (Rust rewrite, nesouvisí)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Projekt má pouze jednu hlavní branch (`main`) lokálně i na remote
- **SC-002**: `git branch -vv` ukazuje pouze `main` s platným tracking na `origin/main`
- **SC-003**: `git status` na `main` ukazuje čistý working tree, up-to-date s remote
- **SC-004**: CI pipeline se spustí při push na `main` a při PR do `main`
- **SC-005**: CLAUDE.md obsahuje sekci s git workflow pravidly (min. 10 řádků)
- **SC-006**: Nová feature branch vytvořená přes speckit má formát `NNN-name` a remote tracking

## Assumptions

- Force-push na `origin/main` je akceptovatelný, protože na projektu pracuje jediný vývojář
- Upstream remote (`genomoncology/biomcp`) zůstává readonly — slouží pouze jako reference
- Speckit `create-new-feature.sh` skript je dostatečný pro vytváření feature branches
- GitHub branch protection rules nejsou aktuálně nastaveny (single developer)
