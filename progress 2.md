# progress.md — CzechMedMCP Session Log

## Session 2026-02-25 (S752-S753)
- Refaktoring a audit bugfixů — PR pushed
- Paralelní cBioPortal+OncoKB fetch, konsolidace PAGE_SIZE konstant
- Deduplikace cBioPortal klientů — sdílený CBioPortalCoreClient
- Oprava kritických bugů — hgvs parametr, rate limiter, consequence_type

## Session 2026-02-25 (S759, S763)
- CLAUDE.md refaktoring a enrichment
- Český překlad dokumentace
- CLI command fixes

## Session 2026-02-26 (S764, S774, S776-S777)
- Tech debt analýza
- Smazáno 40+ nepotřebných souborů (upstream configs, JS, specs, scripts)
- mkdocs.yml, README.md, Makefile cleanup
- CLAUDE.md aktualizováno na post-cleanup stav
- Všech 1025 testů prochází, 0 ruff chyb

## Session 2026-02-26 (S792-S793)
- Server nasazen lokálně na port 8080
- Comprehensive live test: **36/43 nástrojů funkčních**
- Identifikovány problémy: SUKL getter chain, MKN-10 loading, NRPZS 404, SZV/VZP prázdné
- OpenFDA parametry opraveny (drug, name, device)
- Vytvořen test framework v `/tmp/test_biomcp_*.py`

## Session 2026-02-26 (aktuální)
- Přijata CzechMedMCP specifikace v2.1 FINAL
- Vytvořeny plánovací soubory (task_plan.md, findings.md, progress.md)
- Gap analýza: 10 nových nástrojů potřeba, 5 kritických bugů k opravě
