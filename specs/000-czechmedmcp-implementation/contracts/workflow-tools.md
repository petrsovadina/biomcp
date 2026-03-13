# Workflow Tool Contracts

## New Workflow Tools

### czechmed_drug_profile

```python
@mcp_app.tool()
async def czechmed_drug_profile(
    query: Annotated[str, Field(description="Drug name, active substance, or SUKL code")],
) -> str:
    """Complete drug profile: registration + availability + reimbursement + PubMed evidence in one call. Graceful degradation on partial failures."""
```

**Orchestration flow:**
```
1. czechmed_search_drug(query) → extract sukl_code
2. asyncio.gather(return_exceptions=True):
   a. czechmed_get_drug_detail(sukl_code)
   b. czechmed_check_availability(sukl_code)
   c. czechmed_get_reimbursement(sukl_code)
   d. article_searcher(active_substance)  # BioMCP PubMed
3. Assemble sections, mark failed ones with error
```

**Response schema:**
```json
{
  "content": "## Profil léku: Ibuprofen 400mg\n\n### Registrace\n...\n### Dostupnost\n...\n### Úhrada\n...\n### Evidence (PubMed)\n...",
  "structuredContent": {
    "query": "ibuprofen",
    "sukl_code": "0012345",
    "sections": [
      {"section": "registration", "status": "ok", "data": {...}},
      {"section": "availability", "status": "ok", "data": {...}},
      {"section": "reimbursement", "status": "error", "error": "API timeout"},
      {"section": "evidence", "status": "ok", "data": {...}}
    ]
  }
}
```

**Graceful degradation**: Pokud zdroj selže, sekce má `status: "error"` + `error` message. Profil se vrátí vždy — i s jen 1 úspěšnou sekcí.

**Performance target**: <10 sekund celkem (paralelní volání)

### czechmed_diagnosis_assistant

```python
@mcp_app.tool()
async def czechmed_diagnosis_assistant(
    symptoms: Annotated[str, Field(description="Symptom description in Czech")],
    max_candidates: Annotated[int, Field(description="Max diagnosis candidates", ge=1, le=10)] = 5,
) -> str:
    """Diagnostic coding assistant: symptoms → MKN-10 codes + PubMed evidence. Advisory tool with disclaimer."""
```

**Orchestration flow:**
```
1. czechmed_search_diagnosis(symptoms, max_results=max_candidates)
2. For top candidate:
   a. czechmed_get_diagnosis_detail(code) → hierarchy, inclusions
   b. article_searcher(diagnosis_name_en) → PubMed evidence
3. Assemble result with disclaimer
```

**Response schema:**
```json
{
  "content": "## Diagnostická asistence\n\n⚠️ Tento nástroj je pouze podpůrný...\n\n### Kandidáti\n1. J06.9 — Akutní infekce... (skóre: 0.95)\n...\n### Evidence\n...",
  "structuredContent": {
    "query": "akutní zánět hltanu",
    "candidates": [
      {"code": "J06.9", "name_cs": "Akutní infekce horních cest dýchacích", "score": 0.95, "hierarchy": {...}}
    ],
    "evidence": [
      {"pmid": "12345678", "title": "...", "journal": "...", "year": 2024}
    ],
    "disclaimer": "Tento nástroj je pouze podpůrný. Konečná diagnóza je vždy na lékaři."
  }
}
```

**Disclaimer**: MUSÍ být obsažen v každé odpovědi (FR-022). Text: "Tento nástroj je pouze podpůrný. Konečná diagnóza je vždy na lékaři."

### czechmed_referral_assistant

```python
@mcp_app.tool()
async def czechmed_referral_assistant(
    diagnosis_code: Annotated[str, Field(description="MKN-10 code", pattern=r"^[A-Z]\d{2}(\.\d{1,2})?$")],
    city: Annotated[str, Field(description="Patient's city for provider search")],
    max_providers: Annotated[int, Field(description="Max providers to return", ge=1, le=20)] = 10,
) -> str:
    """Referral assistant: diagnosis → relevant specialty → find providers in region with contacts."""
```

**Orchestration flow:**
```
1. czechmed_get_diagnosis_detail(diagnosis_code) → get diagnosis info
2. Map diagnosis chapter/block → recommended specialty (hardcoded mapping table)
3. czechmed_search_provider(city=city, specialty=specialty, page_size=max_providers)
4. Assemble result with diagnosis, specialty, and provider list
```

**Diagnosis → Specialty mapping** (examples):
```
I00-I99 (Nemoci oběhového systému) → "001" (Vnitřní lékařství) / "107" (Kardiologie)
J00-J99 (Nemoci dýchací soustavy) → "001" / "207" (Alergologie)
M00-M99 (Nemoci svalové soustavy) → "001" / "409" (Revmatologie)
```

**Response schema:**
```json
{
  "content": "## Asistence odeslání\n\n**Diagnóza**: I25.1 — ICHS\n**Doporučená odbornost**: Kardiologie\n**Město**: Brno\n\n### Poskytovatelé\n1. Kardiologické centrum Brno...\n",
  "structuredContent": {
    "diagnosis_code": "I25.1",
    "diagnosis_name": "Aterosklerotická nemoc srdeční",
    "recommended_specialty": "Kardiologie",
    "city": "Brno",
    "providers": [
      {"name": "Kardiologické centrum Brno", "address": "...", "phone": "...", "specialties": [...]}
    ]
  }
}
```
