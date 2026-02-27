# BioMCP: Biomedicínský Model Context Protocol

> Fork projektu [genomoncology/biomcp](https://github.com/genomoncology/biomcp) s rozšířením o české zdravotnické datové zdroje.

BioMCP je open source (MIT licence) sada nástrojů, která propojuje AI asistenty a agenty se specializovanými biomedicínskými znalostmi. Postavený na protokolu [Model Context Protocol (MCP)](https://modelcontextprotocol.io/), spojuje AI systémy s autoritativními biomedicínskými datovými zdroji a umožňuje jim odpovídat na otázky o klinických studiích, vědecké literatuře, genomických variantách a českém zdravotnickém systému s přesností a hloubkou.

## Proč BioMCP?.

Velké jazykové modely mají široké obecné znalosti, ale často jim chybí specializované doménové informace nebo přístup k aktuálním zdrojům. BioMCP tento nedostatek překonává pro biomedicínu a české zdravotnictví:

- Poskytuje **strukturovaný přístup** ke klinickým studiím, biomedicínské literatuře, genomickým variantám a českým zdravotnickým registrům
- Umožňuje **dotazy v přirozeném jazyce** na specializované databáze bez znalosti jejich syntaxe
- Podporuje **biomedicínský výzkum** i **české klinické workflows** prostřednictvím jednotného rozhraní
- Funguje jako **MCP server** pro AI asistenty a agenty (Claude Desktop, Cursor, VS Code aj.)

## Biomedicínské datové zdroje

### Literární zdroje

- **PubTator3/PubMed** — recenzovaná biomedicínská literatura s anotacemi entit
- **bioRxiv/medRxiv** — preprintové servery pro biologii a zdravotní vědy
- **Europe PMC** — platforma otevřené vědy včetně preprintů

### Klinické a genomické zdroje

- **ClinicalTrials.gov** — registr a databáze výsledků klinických studií
- **NCI Clinical Trials Search API** — kurátorská databáze onkologických studií NCI
  - Pokročilé filtry (biomarkery, předchozí terapie, mozkové metastázy)
  - Databáze organizací a intervencí
  - Řízený slovník nemocí se synonymy
- **BioThings Suite** — komplexní biomedicínská datová API:
  - **MyVariant.info** — konsolidované anotace genetických variant
  - **MyGene.info** — anotace a informace o genech v reálném čase
  - **MyDisease.info** — ontologie nemocí a synonyma
  - **MyChem.info** — anotace léčiv a chemických látek
- **TCGA/GDC** — The Cancer Genome Atlas pro data o onkologických variantách
- **1000 Genomes** — populační frekvenční data přes Ensembl
- **cBioPortal** — portál genomiky rakoviny s daty o výskytu mutací
- **OncoKB** — znalostní báze precizní onkologie pro klinickou interpretaci variant
  - Terapeutické implikace a FDA-schválené léčby
  - Anotace onkogenicity a efektu mutací
  - Demo server funguje okamžitě bez autentizace (BRAF, ROS1, TP53)

### Regulační a bezpečnostní zdroje

- **OpenFDA** — regulační a bezpečnostní data FDA:
  - **Drug Adverse Events (FAERS)** — postmarketingové zprávy o bezpečnosti léčiv
  - **Drug Labels (SPL)** — oficiální preskripční informace
  - **Device Events (MAUDE)** — nežádoucí příhody zdravotnických prostředků
  - **Drug Approvals** — historie schvalování léčiv FDA
  - **Drug Recalls** — stahování léčiv FDA
  - **Drug Shortages** — aktuální informace o nedostatku léčiv

### Analytické a predikční zdroje

- **AlphaGenome** — predikce efektů variant od Google DeepMind (vyžaduje API klíč)
- **Enrichr** — analýza obohacení genových sad (pathways, ontologie, buněčné typy)

### České zdravotnické zdroje

- **SUKL** — Státní ústav pro kontrolu léčiv
  - Vyhledávání v registru léčiv, detaily, složení
  - Přístup k dokumentům SmPC a příbalové informaci (PIL)
  - Kontrola dostupnosti léčiv na trhu v reálném čase
- **MKN-10** — Mezinárodní klasifikace nemocí, 10. revize
  - Vyhledávání podle kódu i volného textu s podporou diakritiky
  - Procházení celé hierarchie diagnóz (kapitoly, bloky, kategorie)
- **NRPZS** — Národní registr poskytovatelů zdravotních služeb
  - Vyhledávání poskytovatelů podle jména, města, odbornosti
  - Detaily pracovišť s kontaktními údaji
- **SZV** — Seznam zdravotních výkonů
  - Vyhledávání výkonů podle kódu nebo názvu
  - Bodové hodnoty, časové dotace, kódy odborností
- **VZP** — Číselníky Všeobecné zdravotní pojišťovny
  - Prohledávání číselníků výkonů, diagnóz a ATC kódů
  - Detaily položek s pravidly úhrad

Všechny české zdroje jsou veřejná API české státní správy — nevyžadují autentizaci.

## Dostupné MCP nástroje

BioMCP poskytuje 51 specializovaných nástrojů pro biomedicínský výzkum (37 globálních + 14 českých zdravotnických):

### Základní nástroje (3)

#### 1. Nástroj sekvenčního myšlení (Think)

Nástroj `think` by měl být prvním krokem pro každou biomedicínskou výzkumnou úlohu:

```python
think(
    thought="Rozklad dotazu o BRAF mutacích u melanomu...",
    thoughtNumber=1,
    totalThoughts=3,
    nextThoughtNeeded=True
)
```

Pomáhá systematicky rozložit komplexní biomedicínské problémy, naplánovat vícekrokový výzkumný přístup a sledovat průběh analýzy.

#### 2. Nástroj vyhledávání (Search)

Podporuje dva režimy:

##### Unifikovaný dotazovací jazyk (doporučeno)

```python
# Jednoduchý dotaz v přirozeném jazyce
search(query="BRAF melanoma")

# Vyhledávání podle polí
search(query="gene:BRAF AND trials.condition:melanoma")

# Komplexní dotazy
search(query="gene:BRAF AND variants.significance:pathogenic AND articles.date:>2023")

# Schéma prohledávatelných polí
search(get_schema=True)
```

**Podporovaná pole:** `gene:`, `variant:`, `disease:`, `trials.condition:`, `trials.phase:`, `trials.status:`, `trials.intervention:`, `articles.author:`, `articles.journal:`, `articles.date:`, `variants.significance:`, `variants.rsid:`, `variants.frequency:`

##### Doménové vyhledávání

```python
# Vyhledávání článků (automatická integrace cBioPortal)
search(domain="article", genes=["BRAF"], diseases=["melanoma"])

# Vyhledávání studií
search(domain="trial", conditions=["lung cancer"], phase="3")

# Vyhledávání variant
search(domain="variant", gene="TP53", significance="pathogenic")
```

#### 3. Nástroj získání detailů (Fetch)

```python
# Detail článku (PMID i DOI)
fetch(domain="article", id="34567890")
fetch(domain="article", id="10.1101/2024.01.20.23288905")

# Detail studie se všemi sekcemi
fetch(domain="trial", id="NCT04280705", detail="all")

# Detail varianty
fetch(domain="variant", id="rs113488022")
```

### Individuální nástroje (48)

Pro přímý přístup ke specifické funkcionalitě nabízí BioMCP 48 individuálních nástrojů (34 globálních + 14 českých):

#### Nástroje pro články (2)
- **article_searcher** — vyhledávání v PubMed/PubTator3 a preprintech
- **article_getter** — získání detailů článku (PMID i DOI)

#### Nástroje pro klinické studie (6)
- **trial_searcher** — vyhledávání na ClinicalTrials.gov nebo NCI CTS API
- **trial_getter** — získání kompletních detailů studie
- **trial_protocol_getter** — protokol studie
- **trial_references_getter** — publikace ke studii
- **trial_outcomes_getter** — výsledky a míry hodnocení
- **trial_locations_getter** — místa provádění studie

#### Nástroje pro varianty (2)
- **variant_searcher** — vyhledávání v MyVariant.info
- **variant_getter** — získání komprehenzních detailů varianty

#### NCI-specifické nástroje (6)
- **nci_organization_searcher** / **nci_organization_getter** — organizace NCI
- **nci_intervention_searcher** / **nci_intervention_getter** — intervence (léky, přístroje, postupy)
- **nci_biomarker_searcher** — biomarkery v kritériích vhodnosti
- **nci_disease_searcher** — řízený slovník onkologických onemocnění NCI

#### Nástroje pro geny, nemoci a léčiva (3)
- **gene_getter** — informace o genech z MyGene.info
- **disease_getter** — definice nemocí a synonyma z MyDisease.info
- **drug_getter** — informace o léčivech z MyChem.info

#### Nástroje OpenFDA (12)
- **openfda_adverse_searcher** / **openfda_adverse_getter** — nežádoucí účinky (FAERS)
- **openfda_label_searcher** / **openfda_label_getter** — lékové příbalové informace (SPL)
- **openfda_device_searcher** / **openfda_device_getter** — nežádoucí příhody prostředků (MAUDE)
- **openfda_approval_searcher** / **openfda_approval_getter** — schválení léčiv FDA
- **openfda_recall_searcher** / **openfda_recall_getter** — stahování léčiv FDA
- **openfda_shortage_searcher** / **openfda_shortage_getter** — nedostatek léčiv FDA

#### Nástroje genomické analýzy (2)
- **alphagenome_predictor** — predikce efektů variant přes AlphaGenome (vyžaduje API klíč)
- **enrichr_analyzer** — analýza obohacení genových sad přes Enrichr

**Poznámka:** Všechny individuální nástroje vyhledávající podle genu automaticky zahrnují souhrny cBioPortal, když `include_cbioportal=True` (výchozí). Vyhledávání studií může rozšiřovat podmínky o synonyma, když `expand_synonyms=True` (výchozí).

#### České zdravotnické nástroje (14)

##### SUKL — Registr léčiv (5)
- **sukl_drug_searcher** — vyhledávání v českém registru léčiv
- **sukl_drug_getter** — detail léčiva podle kódu SUKL
- **sukl_spc_getter** — Souhrn údajů o přípravku (SmPC)
- **sukl_pil_getter** — Příbalová informace (PIL)
- **sukl_availability_checker** — kontrola dostupnosti léčiva na trhu

##### MKN-10 — Diagnózy (3)
- **mkn_diagnosis_searcher** — vyhledávání diagnóz podle kódu nebo textu
- **mkn_diagnosis_getter** — detail diagnózy s hierarchií
- **mkn_category_browser** — procházení stromu kategorií MKN-10

##### NRPZS — Poskytovatelé zdravotních služeb (2)
- **nrpzs_provider_searcher** — vyhledávání poskytovatelů
- **nrpzs_provider_getter** — detail poskytovatele s pracovišti

##### SZV + VZP — Výkony a pojištění (4)
- **szv_procedure_searcher** — vyhledávání zdravotních výkonů
- **szv_procedure_getter** — detail výkonu s bodovou hodnotou
- **vzp_codebook_searcher** — prohledávání číselníků VZP
- **vzp_codebook_getter** — detail položky číselníku

Všechny české nástroje podporují **transparentní práci s diakritikou** — "leky" najde "léky", "Usti" najde "Ústí".

Podrobná dokumentace českých nástrojů: [docs/czech-tools.md](./docs/czech-tools.md)

## Rychlý start

### Pro uživatele Claude Desktop

1. **Nainstalujte `uv`** (pokud nemáte):

   ```bash
   # MacOS
   brew install uv

   # Windows/Linux
   pip install uv
   ```

2. **Nakonfigurujte Claude Desktop**:
   - Otevřete nastavení Claude Desktop
   - Přejděte do sekce Developer
   - Klikněte na "Edit Config" a přidejte:
   ```json
   {
     "mcpServers": {
       "biomcp": {
         "command": "uv",
         "args": ["run", "--with", "biomcp-python", "biomcp", "run"]
       }
     }
   }
   ```
   - Restartujte Claude Desktop a začněte klást biomedicínské otázky!

### Instalace Python balíčku

```bash
# Pomocí pip
pip install biomcp-python

# Pomocí uv (doporučeno pro rychlejší instalaci)
uv pip install biomcp-python

# Přímé spuštění bez instalace
uv run --with biomcp-python biomcp trial search --condition "lung cancer"
```

## Konfigurace

### Proměnné prostředí

```bash
# Autentizace cBioPortal API (volitelné)
export CBIO_TOKEN="your-api-token"
export CBIO_BASE_URL="https://www.cbioportal.org/api"

# OncoKB (volitelné — demo server funguje automaticky s BRAF, ROS1, TP53)
# export ONCOKB_TOKEN="your-oncokb-token"  # Pro plný přístup ke genům

# Ladění výkonu
export BIOMCP_USE_CONNECTION_POOL="true"   # HTTP connection pooling (výchozí: true)
export BIOMCP_METRICS_ENABLED="false"      # Metriky výkonu (výchozí: false)
```

## Spuštění BioMCP serveru

### Lokální vývoj (STDIO)

```bash
# Výchozí STDIO režim pro lokální vývoj
biomcp run

# Explicitně STDIO
biomcp run --mode stdio
```

### HTTP server

#### Streamable HTTP (doporučeno)

```bash
biomcp run --mode streamable_http

# Vlastní host a port
biomcp run --mode streamable_http --host 127.0.0.1 --port 8080
```

Vlastnosti Streamable HTTP:
- Jediný endpoint `/mcp` pro všechny operace
- Dynamický režim odpovědí (JSON pro rychlé operace, SSE pro dlouhotrvající)
- Plná kompatibilita se specifikací MCP (2025-03-26)
- Lepší škálovatelnost pro cloudové nasazení

#### Starší SSE transport

```bash
biomcp run --mode worker
# Server na http://localhost:8000/sse
```

### Docker

```bash
docker build -t biomcp:latest .
docker run -p 8000:8000 biomcp:latest biomcp run --mode streamable_http
```

## Příkazová řádka (CLI)

BioMCP poskytuje komprehenzní CLI pro přímou interakci s databázemi:

```bash
# Nápověda
biomcp --help

# Spuštění MCP serveru
biomcp run

# Vyhledávání článků
biomcp article search --gene BRAF --disease Melanoma
biomcp article search --gene BRAF --no-preprints
biomcp article get 21717063 --full

# Klinické studie
biomcp trial search --condition "Lung Cancer" --phase PHASE3
biomcp trial search --condition melanoma --source nci --api-key YOUR_KEY
biomcp trial get NCT04280705 Protocol

# Varianty s externími anotacemi
biomcp variant search --gene TP53 --significance pathogenic
biomcp variant get rs113488022
biomcp variant get rs113488022 --no-external

# OncoKB integrace (demo server automaticky)
biomcp variant search --gene BRAF --include-oncokb

# Informace o genech s funkčním obohacením
biomcp gene get TP53 --enrich pathway
biomcp gene get BRCA1 --enrich ontology
biomcp gene get EGFR --enrich celltypes

# NCI-specifické příklady
biomcp organization search "MD Anderson" --api-key YOUR_KEY
biomcp intervention search pembrolizumab --api-key YOUR_KEY
biomcp biomarker search "PD-L1" --api-key YOUR_KEY
biomcp disease search melanoma --source nci --api-key YOUR_KEY

# České zdravotnické příklady
biomcp czech sukl search --query "Ibuprofen"
biomcp czech sukl get "0001234"
biomcp czech sukl availability "0001234"
biomcp czech mkn search --query "J06.9"
biomcp czech mkn browse
biomcp czech nrpzs search --city "Praha" --specialty "kardiologie"
biomcp czech szv search --query "EKG"
biomcp czech vzp search --query "antibiotika"
```

## Testování a ověření

Otestujte nastavení BioMCP pomocí MCP Inspector:

```bash
npx @modelcontextprotocol/inspector uv run --with biomcp-python biomcp run
```

Otevře se webové rozhraní pro prozkoumání a testování všech dostupných nástrojů.

## Příklady použití

### Získání informací o genu

```python
gene_getter(gene_id_or_symbol="TP53")
# Vrací: Oficiální název, souhrn, aliasy, odkazy na databáze
```

### Rozšíření synonym nemoci

```python
# Informace o nemoci se synonymy
disease_getter(disease_id_or_name="GIST")
# Vrací: "gastrointestinal stromal tumor" a další synonyma

# Vyhledávání studií s automatickým rozšířením synonym
trial_searcher(conditions=["GIST"], expand_synonyms=True)
# Prohledává: GIST OR "gastrointestinal stromal tumor" OR "GI stromal tumor"
```

### Integrovaný biomedicínský výzkum

```python
# 1. Začněte myšlením
think(thought="Analýza BRAF V600E u léčby melanomu", thoughtNumber=1)

# 2. Kontext genu
gene_getter("BRAF")

# 3. Vyhledání patogenních variant s klinickou interpretací OncoKB
variant_searcher(gene="BRAF", hgvsp="V600E", significance="pathogenic", include_oncokb=True)

# 4. Nalezení relevantních klinických studií s rozšířením nemocí
trial_searcher(conditions=["melanoma"], interventions=["BRAF inhibitor"])
```

### Kombinace českých a globálních dat

```python
# 1. Najdi lék v SUKL registru
sukl_drug_searcher(query="Ibuprofen")

# 2. Najdi klinické studie pro stejnou účinnou látku
trial_searcher(conditions=["pain"], interventions=["Ibuprofen"])

# 3. Zakóduj diagnózu v MKN-10
mkn_diagnosis_searcher(query="akutní infarkt myokardu")
```

## Dokumentace

### Vývojářské průvodce

- [Průvodce HTTP klientem](./docs/developer-guides/06-http-client-and-caching.md) — Centralizovaný HTTP klient
- [Průvodce zpracováním chyb](./docs/developer-guides/05-error-handling.md) — Vzory zpracování chyb

### České zdravotnické rozšíření

- [Přehled nástrojů](./docs/czech-tools.md) — Dokumentace 14 českých nástrojů
- [Uživatelská příručka](./docs/czech-user-guide.md) — Kompletní příručka pro české uživatele
- [API Reference](./docs/czech-api-reference.md) — Referenční příručka českých API
- [Architektura](./docs/czech-architecture.md) — Technická architektura českých modulů

## Vývoj

### Spouštění testů

```bash
# Všechny testy (včetně integračních)
make test

# Pouze unit testy (bez integračních)
uv run python -m pytest tests -m "not integration"

# Pouze integrační testy
uv run python -m pytest tests -m "integration"
```

**Poznámka:** Integrační testy provádějí reálná API volání a mohou selhat kvůli síťovým problémům nebo omezení přístupu (rate limiting). V CI/CD pipeline běží integrační testy odděleně a jejich selhání neblokuje build.

## Licence

Tento projekt je licencován pod licencí MIT.
