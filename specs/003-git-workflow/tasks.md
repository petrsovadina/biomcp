# Tasks: Git Workflow Systematizace

**Input**: Design documents from `/specs/003-git-workflow/`
**Prerequisites**: plan.md (required), spec.md (required)
**Branch**: `003-git-workflow`

**Tests**: Manuální verifikace git stavů — žádné automatické testy.

**Organization**: Tasky seskupeny dle user stories. Každý story je nezávisle ověřitelný.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Lze spustit paralelně (různé soubory, žádné závislosti)
- **[Story]**: Uživatelský scénář z spec.md (US1–US4)

---

## Phase 1: Setup

**Purpose**: Ověřit výchozí stav před destruktivními git operacemi.

- [ ] T001 Ověřit, že working tree je čistý: `git status` — musí ukazovat 0 dirty files
- [ ] T002 Ověřit, že `python-main` obsahuje vše z `main`: `git log --oneline main..python-main` — musí vrátit commity, `git log --oneline python-main..main` — musí být prázdný
- [ ] T003 Záloha aktuálního stavu: `git tag backup/python-main-final python-main` — pojistka pro rollback

**Checkpoint**: Stav ověřen, záloha vytvořena. Destruktivní operace mohou začít.

---

## Phase 2: US1 — Konsolidace na jednu hlavní branch (Priority: P1) 🎯 MVP

**Goal**: `python-main` obsah → `main`, push na remote, smazat `python-main`

**Independent Test**: `git log --oneline -5 main` ukazuje rename commit, `git push origin main` proběhne bez chyb

- [ ] T004 [US1] Checkout `main` a reset na `python-main` HEAD: `git checkout main && git reset --hard python-main`
- [ ] T005 [US1] Force-push `main` na remote: `git push --force-with-lease origin main`
- [ ] T006 [US1] Smazat lokální `python-main` branch: `git branch -D python-main`
- [ ] T007 [US1] Nastavit tracking `main` → `origin/main`: `git branch --set-upstream-to=origin/main main`
- [ ] T008 [US1] Ověřit: `git log --oneline -5 main` ukazuje rename commit a `git status` ukazuje up-to-date s remote

**Checkpoint**: US1 hotovo — jedna branch `main`, synchronizovaná s remote.

---

## Phase 3: US2 — Vyčištění stale tracking a remote references (Priority: P1)

**Goal**: Žádné stale tracking, žádné orphaned branches

**Independent Test**: `git branch -vv` ukazuje pouze `main` s platným tracking, žádné `[gone]`

- [ ] T009 [US2] Fetch a prune remote refs: `git fetch --all --prune`
- [ ] T010 [US2] Odstranit stale tracking config: `git config --unset branch.claude/sub-pr-2.remote` a `git config --unset branch.claude/sub-pr-2.merge` (a totéž pro `manus-like`, pokud existuje)
- [ ] T011 [US2] Smazat backup tag po úspěšné verifikaci: `git tag -d backup/python-main-final` (volitelné — ponechat jako historický marker)
- [ ] T012 [US2] Ověřit: `git branch -vv` ukazuje pouze `* main` s platným tracking na `origin/main`

**Checkpoint**: US2 hotovo — čistý git stav, žádné stale references.

---

## Phase 4: US4 — Aktualizace CI pipeline (Priority: P2)

**Goal**: CI workflow targetuje `main` místo `python-main`

**Independent Test**: `.github/workflows/ci.yml` obsahuje `branches: [main]` pro push i PR triggers

- [ ] T013 [US4] Aktualizovat `.github/workflows/ci.yml` — změnit branch triggers z `python-main` na `main` pro push i pull_request sekce
- [ ] T014 [US4] Ověřit: `grep -A2 "branches:" .github/workflows/ci.yml` ukazuje `main` (ne `python-main`)

**Checkpoint**: US4 hotovo — CI targetuje správnou branch.

---

## Phase 5: US3 — Dokumentace branching modelu (Priority: P2)

**Goal**: CLAUDE.md obsahuje sekci "Git Workflow" s pravidly

**Independent Test**: CLAUDE.md obsahuje sekci "Git Workflow" s min. 10 řádky

- [ ] T015 [US3] Přidat sekci "Git Workflow" do CLAUDE.md s pravidly:
  - Hlavní branch: `main` (jediná dlouhodobá branch)
  - Feature branches: `NNN-feature-name` (vytvořené přes speckit)
  - Workflow: `/speckit.specify` → `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`
  - Merge: PR do `main` přes `gh pr create`, po merge smazat branch
  - Commit style: conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`)
  - Branch protection: žádná (single developer), PR workflow dobrovolný
- [ ] T016 [P] [US3] Odstranit auto-generated "Active Technologies" sekci z CLAUDE.md (přidanou speckit agent context skriptem) — nepatří do CLAUDE.md
- [ ] T017 [US3] Ověřit: `grep -c "Git Workflow" CLAUDE.md` vrací alespoň 1

**Checkpoint**: US3 hotovo — branching model dokumentován.

---

## Phase 6: Polish & Finální verifikace

**Purpose**: Ověření všech success criteria, commit a cleanup

- [ ] T018 Commitnout všechny změny na feature branch `003-git-workflow`
- [ ] T019 Ověřit SC-001: `git branch -a` — pouze `main` + `remotes/origin/main` (+ aktuální feature branch)
- [ ] T020 Ověřit SC-002: `git branch -vv` — `main` s platným tracking
- [ ] T021 Ověřit SC-003: Working tree čistý po commitu
- [ ] T022 Ověřit SC-004: CI triggers odpovídají `main` branch
- [ ] T023 Ověřit SC-005: CLAUDE.md obsahuje git workflow sekci
- [ ] T024 Mergovat `003-git-workflow` do `main` a smazat feature branch

**Checkpoint**: Všechna SC splněna. Git workflow systematizován.

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup) → Phase 2 (US1: branch konsolidace)
Phase 2 → Phase 3 (US2: stale cleanup) [potřebuje smazaný python-main]
Phase 2 → Phase 4 (US4: CI update) [nezávislé na US2]
Phase 2 → Phase 5 (US3: docs) [nezávislé na US2/US4]
All → Phase 6 (Polish)
```

```
Phase 1 ── Phase 2 (US1) ──┬── Phase 3 (US2: cleanup)
                            ├── Phase 4 (US4: CI)
                            └── Phase 5 (US3: docs)
                                       ↓
                                 Phase 6 (Polish)
```

### Parallel Opportunities

| Tasky | Důvod paralelizace |
|-------|-------------------|
| Phase 4 + Phase 5 | CI update a docs jsou nezávislé po konsolidaci |
| T015 + T016 | Různé sekce CLAUDE.md |

## Implementation Strategy

### MVP First (US1 Only)

1. Phase 1: Setup (T001–T003)
2. Phase 2: Branch konsolidace (T004–T008)
3. **STOP a VALIDATE**: `git log`, `git status`, `git push` — vše funguje
4. Pokračovat na US2–US4 a Polish

### Incremental Delivery

1. Setup + US1 → Jedna main branch, remote aktuální
2. + US2 → Čistý git stav
3. + US4 → CI na správné branch
4. + US3 → Dokumentovaný workflow
5. Polish → Vše ověřeno

---

## Notes

- Phase 2 (US1) obsahuje **destruktivní operace** (force-push, branch delete) — proto backup tag v T003
- T005 používá `--force-with-lease` místo `--force` pro bezpečnější force-push
- T010 čistí stale git config entries — pokud neexistují, příkazy tiše selžou (OK)
- T011 (smazání backup tagu) je volitelné — tag nezabírá místo a slouží jako historický marker
