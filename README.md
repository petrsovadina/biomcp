# CzechMedMCP: AI napojení na české zdravotnictví

Open source MCP server se **60 nástroji** pro české i globální zdravotnické zdroje. Propojuje Claude, Cursor a další AI asistenty s SUKL, MKN-10, PubMed a dalšími databázemi.

**[Dokumentace](https://czech-med-mcp-docs.vercel.app)** · **[GitHub](https://github.com/petrsovadina/CzechMedMCP)**

## Rychlý startů

```bash
# Instalace z GitHubu
uv tool install git+https://github.com/petrsovadina/CzechMedMCP.git
```

### Claude Desktop / Cursor / VS Code...

Přidejte do konfigurace MCP serverů:

```json
{
  "mcpServers": {
    "czechmedmcp": {
      "command": "czechmedmcp",
      "args": ["run"]
    }
  }
}
```

### Remote HTTP server

Pro vzdálený přístup (produkce běží na Railway):

```bash
czechmedmcp run --mode streamable_http --host 0.0.0.0 --port 8000
```

### MCP Inspector (testování)

```bash
npx @modelcontextprotocol/inspector czechmedmcp run
```

## Katalog nástrojů (60)

### České zdravotnické nástroje (23)

| Modul | Nástrojů | Popis |
|-------|----------|-------|
| SUKL | 8 | Registr léčiv, SPC/PIL, dostupnost, lékárny |
| MKN-10 | 4 | Diagnózy, hierarchie, statistiky |
| NRPZS | 3 | Poskytovatelé zdravotních služeb |
| SZV | 3 | Zdravotní výkony, kalkulace úhrad |
| VZP | 2 | Úhrady léčiv, porovnání alternativ |
| Workflow | 3 | Drug profile, diagnosis assist, referral assist |

### Globální biomedicínské nástroje (37)

| Modul | Nástrojů | Zdroj |
|-------|----------|-------|
| Články | 2 | PubMed, PubTator3, bioRxiv, Europe PMC |
| Klinické studie | 6 | ClinicalTrials.gov, NCI CTS API |
| Genomické varianty | 3 | MyVariant.info, cBioPortal, OncoKB |
| Geny, nemoci, léčiva | 3 | MyGene, MyDisease, MyChem |
| NCI | 6 | NCI Thesaurus (organizace, intervence, biomarkery) |
| OpenFDA | 12 | Nežádoucí účinky, labely, přístroje, schválení |
| Obohacení | 1 | Enrichr (genové sady) |
| Utility | 4 | Unified search, fetch, think, metrics |

## Konfigurace

```bash
cp .env.example .env
```

| Proměnná | Popis | Povinná |
|----------|-------|---------|
| `NCI_API_KEY` | API klíč pro NCI Clinical Trials | Ne |
| `OPENFDA_API_KEY` | API klíč pro OpenFDA | Ne |
| `ONCOKB_TOKEN` | Token pro OncoKB | Ne |
| `ALPHAGENOME_API_KEY` | API klíč pro AlphaGenome | Ne |

České zdravotnické nástroje **nevyžadují žádné API klíče** — všechna data jsou veřejná.

## Vývoj

```bash
# Instalace a nastavení
uv sync --all-extras && uv run pre-commit install

# Spuštění testů
uv run python -m pytest -x --ff -n auto --dist loadscope

# Lint + formátování
uv run ruff check src tests && uv run ruff format src tests

# Kompletní kontrola kvality
make check
```

## Deployment

| Komponenta | Platforma | Konfigurace |
|---|---|---|
| MCP Server | Railway | `Dockerfile`, `railway.json` |
| MCP Server | Arcade Cloud | `arcade deploy -e src/czechmedmcp/arcade/entrypoint.py` |
| Landing page | Vercel | root directory `apps/` |
| Dokumentace | Vercel | [czech-med-mcp-docs.vercel.app](https://czech-med-mcp-docs.vercel.app) |

### Docker (lokální)

```bash
docker compose up --build
# MCP endpoint: http://localhost:8000/mcp
# Health:       http://localhost:8000/health
```

### Railway

Push na `main` spustí auto-deploy (CI musí projít). Konfigurace:

- `Dockerfile` — Python 3.11-slim, `.[worker]` extras
- `railway.json` — healthcheck na `/health`, restart on failure
- Env vars: `MCP_MODE=streamable_http`, `PORT` nastavuje Railway automaticky

Ruční deploy:

```bash
railway up --detach
```

### Arcade Cloud

Alternativní deployment přes [Arcade](https://arcade.dev) — spravovaná platforma s auth, discovery a multi-user přístupem:

```bash
# Instalace CLI
uv tool install arcade-mcp

# Login + deploy (60 nástrojů)
arcade login
arcade deploy -e src/czechmedmcp/arcade/entrypoint.py

# PoC deploy (5 nástrojů pro validaci)
arcade deploy -e src/czechmedmcp/arcade/poc_entrypoint.py
```

Arcade vyžaduje optional dependency: `uv sync --extra arcade`

### Vercel (web + docs)

Obě Next.js aplikace se deployují automaticky z monorepa:

- **Landing page**: root directory `apps/`, framework Next.js
- **Dokumentace**: root directory `apps/docs`, static export (`output: 'export'`)

## Licence

MIT — plná svoboda komerčního využití.
