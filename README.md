# CzechMedMCP: AI napojení na české zdravotnictví

Open source MCP server se **60 nástroji** pro české i globální zdravotnické zdroje. Propojuje Claude, Cursor a další AI asistenty s SUKL, MKN-10, PubMed a dalšími databázemi.

**[Landing page](https://web-sovadina.vercel.app)** · **[GitHub](https://github.com/petrsovadina/biomcp)**

## Rychlý start

```bash
pip install czechmedmcp
```

### Claude Desktop / Cursor / VS Code

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

### Spuštění serveru

```bash
# STDIO (lokální vývoj, Claude Desktop)
czechmedmcp run

# HTTP (remote, Medevio integrace)
czechmedmcp run --mode streamable_http --host 0.0.0.0 --port 8080
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

# Spuštění testů (736 testů)
uv run python -m pytest -x --ff -n auto --dist loadscope

# Lint + formátování
uv run ruff check src tests && uv run ruff format src tests

# Kompletní kontrola kvality
make check
```

## Licence

MIT — plná svoboda komerčního využití.

---

*Postaveno pro [Medevio](https://medevio.com) — AI asistent pro české lékaře.*
*Založeno na [BioMCP](https://github.com/genomoncology/biomcp) (MIT).*
