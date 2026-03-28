---
color: green
isContextNode: false
agent_name: Amy
---
# MKN-10 + Diagnosis Assist — Hybrid Search

MKN-10 search s Czech synonym dictionary (130+ termů) + 4-fázový hybrid diagnosis searcher s oncology demotion.

### MKN-10 Search
```
_mkn_search(query)
  ├─ CODE_RE match? → prefix scan
  └─ Text: synonym lookup → text index → merge + dedup
```
Synonym dict: "cukrovka"→E11/E10, "mrtvice"→I64, "astma"→J45 atd. Prevalence boost: E11 (Type 2) rank > E10 (Type 1).

### Diagnosis Assist — 4-Phase Hybrid
```
search_diagnoses(symptoms)
  Phase 1: Cluster matching (multi-keyword, score 0.80-0.95)
  Phase 2: Per-token exact(1.0)/fuzzy(0.7)/text(0.4)
  Phase 3: Oncology demotion for metabolic queries (C/D × 0.5)
  Merge → dedup by code → enrich names → top N
```

### Workflows
- **drug_profile**: resolve SUKL code → parallel fetch (detail+avail+reimb+PubMed) → DrugProfile
- **referral_assistant**: MKN chapter letter → specialty (20 mappings) → NRPZS search
- **diagnosis_assistant**: hybrid search → PubMed evidence (top 3) → match type indicators (✓✓/✓/~)

### NOTES

- Two synonym systems: CZ_MEDICAL_SYNONYMS (colloquial→ICD) vs SYMPTOM_CLUSTER_MAP (multi-keyword→ICD+boost) — don't confuse
- Synonym dict is hardcoded (130+ terms) — rozsšíření = edit synonyms.py
- Module-level globals (None → lazy init) are NOT thread-safe but OK for asyncio single-thread

deep dive [[czech-overview]]
