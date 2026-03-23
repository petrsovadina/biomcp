# Feature Specification: Deployment Cleanup

**Feature Branch**: `005-deployment-cleanup`
**Created**: 2026-03-16
**Status**: Completed
**Input**: Odstranění mrtvých deployment konfigurací (Fly.io, Docker Compose prod, Caddyfile), konsolidace Dockerfiles, příprava Vercel pro web a docs aplikace.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Odstranění mrtvých konfigurací (Priority: P1)

Jako maintainer chci, aby repozitář neobsahoval nepoužívané deployment konfigurace, abych nemusel udržovat kód, který nikdo nepoužívá, a noví přispěvatelé nebyli zmateni množstvím alternativních deployment cest.

**Why this priority**: Mrtvý kód zvyšuje kognitivní zátěž a maintenance burden. Každá nepoužívaná konfigurace je potenciální zdroj zastaralých informací a falešného pocitu, že je „připravená k použití".

**Independent Test**: Po odstranění souborů repozitář neobsahuje `fly.toml`, `docker-compose.prod.yml` a `Caddyfile`. Existující Railway deployment zůstává funkční.

**Acceptance Scenarios**:

1. **Given** repozitář obsahuje `fly.toml`, `docker-compose.prod.yml` a `Caddyfile`, **When** maintainer provede cleanup, **Then** tyto soubory jsou odstraněny z repozitáře
2. **Given** repozitář obsahuje dva Dockerfiles (`Dockerfile` a `Dockerfile.railway`), **When** maintainer provede konsolidaci, **Then** existuje pouze jeden `Dockerfile` (původní `Dockerfile.railway`)
3. **Given** Railway deployment je aktivní a zdravý, **When** cleanup je dokončen, **Then** produkční deployment zůstává nezměněn a funkční

---

### User Story 2 — Konsolidace Dockerfile (Priority: P1)

Jako maintainer chci mít jeden jasný Dockerfile pro produkční nasazení, aby bylo zřejmé, jak se projekt buildí a nasazuje.

**Why this priority**: Dva Dockerfiles způsobují zmatek. Hlavní `Dockerfile` buildí i Next.js web, který se nyní nasazuje samostatně — je tedy zastaralý.

**Independent Test**: Existuje jediný `Dockerfile`, který je použitelný pro Railway deployment. Build proběhne úspěšně.

**Acceptance Scenarios**:

1. **Given** `Dockerfile.railway` je funkční pro produkční nasazení, **When** je přejmenován na `Dockerfile`, **Then** Docker build projde úspěšně
2. **Given** `railway.json` odkazuje na `Dockerfile.railway`, **When** Dockerfile je přejmenován, **Then** `railway.json` je aktualizován a odkazuje na `Dockerfile`
3. **Given** `docker-compose.yml` (lokální vývoj) existuje, **When** konsolidace je dokončena, **Then** `docker-compose.yml` funguje s novým `Dockerfile`

---

### User Story 3 — Aktualizace dokumentace (Priority: P2)

Jako maintainer chci, aby CLAUDE.md, README a ostatní dokumentace odrážely skutečný stav deployment architektury — jeden Dockerfile pro Railway, web a docs na Vercel.

**Why this priority**: Zastaralá dokumentace je horší než žádná. Nový přispěvatel by neměl nacházet zmínky o Fly.io nebo Docker Compose prod.

**Independent Test**: CLAUDE.md a README neobsahují zmínky o odstraněných konfiguracích.

**Acceptance Scenarios**:

1. **Given** CLAUDE.md obsahuje sekce o Fly.io, Docker Compose prod a Caddyfile, **When** dokumentace je aktualizována, **Then** tyto sekce jsou odstraněny a nahrazeny aktuální architekturou (Railway + Vercel)
2. **Given** README popisuje deployment možnosti, **When** dokumentace je aktualizována, **Then** README popisuje pouze Railway (server) a Vercel (web + docs)

---

### User Story 4 — Příprava Vercel pro web a docs (Priority: P2)

Jako maintainer chci, aby landing page (`apps/web/`) a dokumentace (`apps/docs/`) byly připraveny k nasazení na Vercel s funkčním buildem.

**Why this priority**: Obě aplikace jsou statické Next.js projekty. Připravení repozitáře zajistí hladké propojení s Vercel.

**Independent Test**: Obě aplikace buildí lokálně přes `npm run build:web` a `npm run build:docs`. Vercel konfigurace je přítomna.

**Acceptance Scenarios**:

1. **Given** `apps/web/` je Next.js 15 aplikace, **When** se spustí build, **Then** build projde úspěšně bez chyb
2. **Given** `apps/docs/` je Nextra aplikace se statickým exportem, **When** se spustí build, **Then** build projde úspěšně a vygeneruje statické HTML
3. **Given** obě aplikace mají `vercel.json` konfiguraci, **When** maintainer připojí repo na Vercel, **Then** Vercel detekuje monorepo strukturu a umožní deploy obou projektů

---

### Edge Cases

- Co když Railway deployment selže po přejmenování Dockerfile? → `railway.json` musí být aktualizován současně s přejmenováním
- Co když `docker-compose.yml` odkazuje na jiný Dockerfile? → Ověřit a aktualizovat referenci
- Co když někdo potřebuje self-hosted deployment? → Dokumentovat, že projekt je optimalizován pro Railway + Vercel; self-hosted je možný přes Docker
- Co když Vercel build selže kvůli chybějícím závislostem v monorepu? → Ověřit, že obě apps buildí nezávisle

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Repozitář NESMÍ obsahovat `fly.toml` po dokončení cleanup
- **FR-002**: Repozitář NESMÍ obsahovat `docker-compose.prod.yml` po dokončení cleanup
- **FR-003**: Repozitář NESMÍ obsahovat `Caddyfile` po dokončení cleanup
- **FR-004**: Repozitář NESMÍ obsahovat `Dockerfile.railway` — MUSÍ existovat pouze jeden `Dockerfile`
- **FR-005**: Původní multi-stage `Dockerfile` (s Next.js buildem) MUSÍ být odstraněn
- **FR-006**: `railway.json` MUSÍ odkazovat na `Dockerfile` (ne `Dockerfile.railway`)
- **FR-007**: `docker-compose.yml` MUSÍ být zachován pro lokální vývoj a MUSÍ fungovat s novým `Dockerfile`
- **FR-008**: CLAUDE.md MUSÍ odrážet aktuální deployment architekturu
- **FR-009**: README MUSÍ popisovat aktuální deployment architekturu
- **FR-010**: CI/CD pipeline MUSÍ zůstat funkční po všech změnách
- **FR-011**: Railway produkční deployment NESMÍ být narušen změnami
- **FR-012**: Obě Next.js aplikace MUSÍ mít funkční build (`npm run build:web`, `npm run build:docs`)

### Assumptions

- Railway deployment používá `railway up` přes CLI — Dockerfile cesta je v `railway.json`
- Vercel propojení s GitHub bude provedeno ručně přes Vercel dashboard (mimo scope tohoto spec)
- `docker-compose.yml` pro lokální vývoj zůstává užitečný a bude zachován
- Historické reference na BioMCP v CHANGELOG.md a specs/ zůstanou — jedná se o historii, ne aktivní konfiguraci
- `.env.example` zůstane beze změn — obsahuje konfiguraci relevantní pro všechny prostředí

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Repozitář obsahuje přesně 1 Dockerfile (ne 2)
- **SC-002**: 0 souborů spojených s Fly.io deployment (`fly.toml`)
- **SC-003**: 0 souborů spojených s produkčním Docker Compose (`docker-compose.prod.yml`, `Caddyfile`)
- **SC-004**: Railway produkce vrací `{"status":"healthy"}` na `/health` endpoint po merge
- **SC-005**: `npm run build:web` a `npm run build:docs` projdou bez chyb
- **SC-006**: CLAUDE.md a README neobsahují zmínky o `fly.toml`, `docker-compose.prod.yml` ani `Caddyfile`
