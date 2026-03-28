---
color: crimson
isContextNode: false
agent_name: Aki
status: claimed
---
# Czech Healthcare Modules

23 nástrojů pro české zdravotnictví — SUKL (léky, lékárny), MKN-10 (diagnózy), NRPZS (poskytovatelé), SZV (výkony), VZP (úhrady), diagnosis assist.

**Root path:** `src/czechmedmcp/czech/`

**Submodules:** sukl/ (DrugIndex, DLP API), mkn/ (ICD-10 CZ, synonymy, stats), nrpzs/ (registr poskytovatelů), szv/ (seznam výkonů), vzp/ (úhrady), diagnosis_embed/ (FAISS embeddings), workflows/ (diagnosis_assistant, referral_assist)

**Purpose:** Propojení AI asistentů s českými zdravotnickými registry a databázemi. SUKL DrugIndex = in-memory index 68K léků.

[[welcome_to_voicetree]]
