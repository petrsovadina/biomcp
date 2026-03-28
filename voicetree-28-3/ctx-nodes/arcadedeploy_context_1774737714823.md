---
isContextNode: true
containedNodeIds:
  - /Users/petrsovadina/Desktop/Develope/personal/CzechMed-MCP/voicetree-28-3/arcadedeploy.md
  - /Users/petrsovadina/Desktop/Develope/personal/CzechMed-MCP/voicetree-28-3/welcome_to_voicetree.md
  - /Users/petrsovadina/Desktop/Develope/personal/CzechMed-MCP/voicetree-28-3/run_me.md
  - /Users/petrsovadina/Desktop/Develope/personal/CzechMed-MCP/voicetree-28-3/hover_over_me.md
  - /Users/petrsovadina/Desktop/Develope/personal/CzechMed-MCP/voicetree-28-3/welcome_to.md
  - /Users/petrsovadina/Desktop/Develope/personal/CzechMed-MCP/voicetree-28-3/climodule.md
  - /Users/petrsovadina/Desktop/Develope/personal/CzechMed-MCP/voicetree-28-3/frontendapps.md
  - /Users/petrsovadina/Desktop/Develope/personal/CzechMed-MCP/voicetree-28-3/coreinfrastructure.md
  - /Users/petrsovadina/Desktop/Develope/personal/CzechMed-MCP/voicetree-28-3/routertools.md
  - /Users/petrsovadina/Desktop/Develope/personal/CzechMed-MCP/voicetree-28-3/czechhealthcare.md
  - /Users/petrsovadina/Desktop/Develope/personal/CzechMed-MCP/voicetree-28-3/biomedicaldomains.md
---
# ctx
Nearby nodes to: /Users/petrsovadina/Desktop/Develope/personal/CzechMed-MCP/voicetree-28-3/arcadedeploy.md
```
Arcade Deploy Layer
└── Voicetree
    ├── Generate codebase graph (run me)
    ├── Hover over me
    ├── Hello
    ├── CLI & Server Modes
    ├── Frontend Apps (Web + Docs)
    ├── Core & Infrastructure
    ├── Router & Tool Registration
    ├── Czech Healthcare Modules
    └── Biomedical Domain Modules
```

## Node Contents 
- **Voicetree** (/Users/petrsovadina/Desktop/Develope/personal/CzechMed-MCP/voicetree-28-3/welcome_to_voicetree.md)
  # Voicetree
## The spatial IDE for multi-agent orchestration
##### Build massive projects out of hundreds of agent sessions whose outputs are all saved, connected together, and turned into a Markdown mindmap. Spatially navigate the graph to hand-hold agents as they recursively fork themselves.
Optimise for seeing only the most relevant information at the necessary level of abstraction.
ready? [\[run_me.md]\]
explore the features [\[hover_over_me.md]\]
- **Generate codebase graph (run me)** (/Users/petrsovadina/Desktop/Develope/personal/CzechMed-MCP/voicetree-28-3/run_me.md)
  # Generate codebase graph (run me)
### Your task is to run the following workflow
1. **Quick scan** — identify the top ~7 major modules using lightweight exploration only (glob directory listings, read a few entry points). Do NOT deep-dive into any module. The goal is just module names, root paths, and a one-line purpose each.
2. **Create a skeleton node** for each module containing only:
    - Module name and root path
    - One-line purpose
    - A distinct color per module (submodules inherit color)
3. **Spawn one voicetree agent per module**. Each agent is responsible for:
    - Deep-exploring its module (read key files, trace flows)
    - Updating its parent node with: concise purpose summary, mermaid diagram for core flow, notable gotchas or tech debt
  ...7 additional lines
- **Hover over me** (/Users/petrsovadina/Desktop/Develope/personal/CzechMed-MCP/voicetree-28-3/hover_over_me.md)
  # Hover over me
Recommended usage for agentic engineering:
1. Brainstorm a large task in the mindmap itself. Get AI to help review and suggest options as needed.
2. Start executing agents on branches of the brainstorm. For larger/harder parts of the project, Tell agents to "decompose plan into a dependency graph of nodes, and then spawn voicetree agents to work through it"
3. Rotate between the idle agents (cmd + [\[ keyboard shortcut), to see if they need help or to be nudged towards true completion.
4. Since the feature will never be pixel perfect on the first iteration, for running next steps, spawn agents directly on handover notes automatically created by the previous sessions.
5. Zoom out to see the big picture of the shape of the work you and your agents did, useful for identifying productivity bottlenecks.
### Voicetree features
Above the node editor, you will see 6 buttons, these are all the actions you can perform on a node. Try adding a child node now.
Markdown support:
  ...46 additional lines
- **Hello** (/Users/petrsovadina/Desktop/Develope/personal/CzechMed-MCP/voicetree-28-3/welcome_to.md)
  # Hello
welcome to [\[welcome_to_voicetree.md]\]
- **CLI & Server Modes** (/Users/petrsovadina/Desktop/Develope/personal/CzechMed-MCP/voicetree-28-3/climodule.md)
  # CLI & Server Modes
Typer CLI app se třemi serverovými režimy (stdio, streamable_http, worker) a doménovými sub-příkazy.
**Root path:** `src/czechmedmcp/cli/`
**Key files:** server.py, __init__.py + per-domain CLI subcommands
**Purpose:** Entry point přes __main__.py → Typer app. Tři režimy: STDIO (Claude Desktop), HTTP endpoint (Railway), Legacy SSE worker.
[\[welcome_to_voicetree]\]
- **Frontend Apps (Web + Docs)** (/Users/petrsovadina/Desktop/Develope/personal/CzechMed-MCP/voicetree-28-3/frontendapps.md)
  # Frontend Apps (Web + Docs)
Next.js 15 landing page (apps/web/) a Nextra 4 dokumentace (apps/docs/) v Turborepo monorepu.
**Root path:** `apps/web/` + `apps/docs/`
**Tech:** Next.js 15, React 19, Nextra 4, Tailwind, Turborepo orchestrace
**Purpose:** Landing page pro CzechMedMCP projekt a interaktivní dokumentace. Deploy na Vercel. Node 20.x (pinováno kvůli @napi-rs/simple-git bug).
[\[welcome_to_voicetree]\]
- **Core & Infrastructure** (/Users/petrsovadina/Desktop/Develope/personal/CzechMed-MCP/voicetree-28-3/coreinfrastructure.md)
  # Core & Infrastructure
Základní vrstva: FastMCP singleton, HTTP klient s cache/retry/circuit breaker, konstanty, výjimky, rate limiter, connection pool, utils.
**Root path:** `src/czechmedmcp/` (top-level .py files) + `src/czechmedmcp/utils/`
**Key files:** core.py, constants.py, exceptions.py, http_client.py, auth.py, circuit_breaker.py, connection_pool.py, rate_limiter.py, retry.py, render.py, metrics.py
**Purpose:** Sdílená infrastruktura pro všechny doménové moduly — HTTP pipeline (cache → circuit breaker → retry → parse), FastMCP app singleton, Pydantic helpers, markdown rendering.
[\[welcome_to_voicetree]\]
- **Router & Tool Registration** (/Users/petrsovadina/Desktop/Develope/personal/CzechMed-MCP/voicetree-28-3/routertools.md)
  # Router & Tool Registration
Registrace 60 MCP nástrojů, unified search/fetch dispatcher přes 20+ domén, query parsing a parameter routing.
**Root path:** `src/czechmedmcp/` — router.py, router_handlers.py, fetch_handlers.py, individual_tools.py, thinking_tool.py, query_parser.py, parameter_parser.py, domain_handlers.py
**Purpose:** Dva unifikované nástroje (search + fetch) jako dispatcher + 33 individuálních nástrojů + thinking tool + metrics handler. Router je 733-řádková god function s noqa: C901.
[\[welcome_to_voicetree]\]
- **Czech Healthcare Modules** (/Users/petrsovadina/Desktop/Develope/personal/CzechMed-MCP/voicetree-28-3/czechhealthcare.md)
  # Czech Healthcare Modules
23 nástrojů pro české zdravotnictví — SUKL (léky, lékárny), MKN-10 (diagnózy), NRPZS (poskytovatelé), SZV (výkony), VZP (úhrady), diagnosis assist.
**Root path:** `src/czechmedmcp/czech/`
**Submodules:** sukl/ (DrugIndex, DLP API), mkn/ (ICD-10 CZ, synonymy, stats), nrpzs/ (registr poskytovatelů), szv/ (seznam výkonů), vzp/ (úhrady), diagnosis_embed/ (FAISS embeddings), workflows/ (diagnosis_assistant, referral_assist)
**Purpose:** Propojení AI asistentů s českými zdravotnickými registry a databázemi. SUKL DrugIndex = in-memory index 68K léků.
[\[welcome_to_voicetree]\]
- **Biomedical Domain Modules** (/Users/petrsovadina/Desktop/Develope/personal/CzechMed-MCP/voicetree-28-3/biomedicaldomains.md)
  # Biomedical Domain Modules
Doménové moduly pro PubMed články, klinické studie, varianty, geny, léky, nemoci, biomarkery, OpenFDA, Enrichr, cBioPortal.
**Root path:** `src/czechmedmcp/` — articles/, trials/, variants/, genes/, drugs/, diseases/, biomarkers/, enrichr/, interventions/, organizations/, openfda/, integrations/
**Purpose:** 33 standardních biomedicínských nástrojů přistupujících k PubMed, ClinicalTrials.gov, MyVariant.info, OpenFDA, cBioPortal, OncoKB, NCI, Enrichr. Každý modul má search.py + getter.py pattern.
[\[welcome_to_voicetree]\]
<TASK> IMPORTANT. YOUR specific task, and the most relevant context is the source note you were spawned from, which is:
        /Users/petrsovadina/Desktop/Develope/personal/CzechMed-MCP/voicetree-28-3/arcadedeploy.md: # Arcade Deploy Layer

Paralelní deployment wrappery pro Arcade Cloud — 60 nástrojů delegujících na stejné privátní implementace jako FastMCP.

**Root path:** `src/czechmedmcp/arcade/`

**Key files:** entrypoint.py, poc_entrypoint.py, individual_tools.py, czech_tools.py, router_tools.py, thinking_tool.py

**Purpose:** Arcade-MCP-Server SDK wrappery. Klíčové rozdíly: @arcade_app.tool (bez závorek), Annotated[type, 'desc'] místo Field(), manuální clamping místo Pydantic constraints.

[\[welcome_to_voicetree]\]
 </TASK>

