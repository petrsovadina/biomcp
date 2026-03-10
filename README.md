# CzechMedMCP: Český zdravotnický MCP server

> Fork projektu [genomoncology/biomcp](https://github.com/genomoncology/biomcp) rozšířený o české zdravotnické datové zdroje pro platformu [Medevio](https://medevio.com)...

CzechMedMCP je open source (MIT) MCP server se **60 biomedicínskými a zdravotnickými nástroji** — 23 českých + 37 globálních. Postavený na [Model Context Protocol](https://modelcontextprotocol.io/), slouží jako datová vrstva pro AI asistenty lékařů.

## Rychlý start

### Instalace

```bash
pip install biomcp-python
# nebo
uv pip install biomcp-python
```

### Claude Desktop / Cursor / VS Code

Přidejte do konfigurace MCP serverů:

```json
{
  "mcpServers": {
    "czechmedmcp": {
      "command": "uv",
      "args": ["run", "--with", "biomcp-python", "biomcp", "run"]
    }
  }
}
```

### Spuštění serveru

```bash
# STDIO (lokální vývoj, Claude Desktop)
biomcp run

# HTTP (remote, Medevio integrace)
biomcp run --mode streamable_http --host 0.0.0.0 --port 8080
```

### MCP Inspector (testování)

```bash
npx @modelcontextprotocol/inspector uv run --with biomcp-python biomcp run
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

## Dokumentace

Kompletní dokumentace je dostupná na [docs-site](https://petrsovadina.github.io/biomcp/):

- [Uživatelská příručka](https://petrsovadina.github.io/biomcp/czech-user-guide/)
- [API Reference](https://petrsovadina.github.io/biomcp/czech-api-reference/)
- [Architektura](https://petrsovadina.github.io/biomcp/czech-architecture/)
- [Přehled nástrojů](https://petrsovadina.github.io/biomcp/czech-tools/)

## Licence

MIT — plná svoboda komerčního využití.

---

*CzechMedMCP je fork [BioMCP](https://github.com/genomoncology/biomcp) (MIT) rozšířený o české zdravotnické zdroje.*
*GitHub: [petrsovadina/biomcp](https://github.com/petrsovadina/biomcp)*
