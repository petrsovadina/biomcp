"""Symptom-to-MKN-10 mapping dictionary.

Maps ~100 common Czech and English symptom phrases to
relevant MKN-10 code prefixes.  Used by the hybrid
diagnosis searcher to bridge the gap between lay symptom
descriptions ("bolest hlavy") and clinical terminology
("cefalea", G43/G44/R51).
"""

from czechmedmcp.czech.diacritics import normalize_query

# Each key is a normalized (lower, no diacritics) symptom
# phrase; values are MKN-10 code prefixes that the phrase
# maps to.  Both CZ and EN variants are included.
SYMPTOM_MKN_MAP: dict[str, list[str]] = {
    # --- Bolest / Pain ---
    "bolest hlavy": ["G43", "G44", "R51"],
    "headache": ["G43", "G44", "R51"],
    "cefalea": ["G43", "G44", "R51"],
    "migréna": ["G43"],
    "migrena": ["G43"],
    "migraine": ["G43"],
    "bolest břicha": ["R10", "K25", "K29"],
    "bolest bricha": ["R10", "K25", "K29"],
    "abdominal pain": ["R10", "K25", "K29"],
    "bolest na hrudi": ["R07", "I20", "I21"],
    "chest pain": ["R07", "I20", "I21"],
    "bolest v krku": ["J02", "J06"],
    "sore throat": ["J02", "J06"],
    "bolest zad": ["M54"],
    "back pain": ["M54"],
    "bolest kloubů": ["M25", "M13"],
    "bolest kloubu": ["M25", "M13"],
    "joint pain": ["M25", "M13"],
    "bolest ucha": ["H92", "H66"],
    "ear pain": ["H92", "H66"],
    "bolest zubu": ["K08"],
    "toothache": ["K08"],
    "bolest svalu": ["M79"],
    "muscle pain": ["M79"],
    "bolest kolene": ["M25.5"],
    "knee pain": ["M25.5"],
    # --- Horečka / Fever ---
    "horečka": ["R50"],
    "horecka": ["R50"],
    "fever": ["R50"],
    "teplota": ["R50"],
    "subfebrilie": ["R50"],
    # --- Dýchací / Respiratory ---
    "kašel": ["R05", "J06", "J20"],
    "kasel": ["R05", "J06", "J20"],
    "cough": ["R05", "J06", "J20"],
    "dušnost": ["R06", "J45", "J44"],
    "dusnost": ["R06", "J45", "J44"],
    "dyspnea": ["R06", "J45", "J44"],
    "shortness of breath": ["R06", "J45", "J44"],
    "rýma": ["J00"],
    "ryma": ["J00"],
    "rhinitis": ["J00", "J30"],
    "runny nose": ["J00"],
    "bolest v hrdle": ["J02", "J06"],
    "chrapot": ["R49"],
    "hoarseness": ["R49"],
    "chřipka": ["J10", "J11"],
    "chripka": ["J10", "J11"],
    "flu": ["J10", "J11"],
    "influenza": ["J10", "J11"],
    # --- GIT / Gastrointestinal ---
    "nausea": ["R11"],
    "nauzea": ["R11"],
    "zvracení": ["R11"],
    "zvraceni": ["R11"],
    "vomiting": ["R11"],
    "průjem": ["K52", "A09"],
    "prujem": ["K52", "A09"],
    "diarrhea": ["K52", "A09"],
    "zácpa": ["K59"],
    "zacpa": ["K59"],
    "constipation": ["K59"],
    "pálení žáhy": ["K21"],
    "paleni zahy": ["K21"],
    "heartburn": ["K21"],
    "nadýmání": ["R14"],
    "nadymani": ["R14"],
    "bloating": ["R14"],
    "flatulence": ["R14"],
    # --- Kůže / Skin ---
    "vyrážka": ["R21", "L50"],
    "vyrazka": ["R21", "L50"],
    "rash": ["R21", "L50"],
    "svědění": ["L29"],
    "svedeni": ["L29"],
    "itching": ["L29"],
    "pruritus": ["L29"],
    "ekzém": ["L30"],
    "ekzem": ["L30"],
    "eczema": ["L30"],
    # --- Neurologie / Neurology ---
    "závrať": ["R42", "H81"],
    "zavrat": ["R42", "H81"],
    "dizziness": ["R42", "H81"],
    "vertigo": ["R42", "H81"],
    "nespavost": ["G47", "F51"],
    "insomnia": ["G47", "F51"],
    "mdloba": ["R55"],
    "syncope": ["R55"],
    "fainting": ["R55"],
    "třes": ["R25"],
    "tres": ["R25"],
    "tremor": ["R25"],
    "znecitlivění": ["R20"],
    "znecitliveni": ["R20"],
    "numbness": ["R20"],
    "brnění": ["R20"],
    "brneni": ["R20"],
    "tingling": ["R20"],
    # --- Psychika / Psychiatry ---
    "úzkost": ["F41"],
    "uzkost": ["F41"],
    "anxiety": ["F41"],
    "deprese": ["F32", "F33"],
    "depression": ["F32", "F33"],
    "neklid": ["R45"],
    "agitation": ["R45"],
    "stres": ["F43"],
    "stress": ["F43"],
    # --- Celkové / General ---
    "únava": ["R53"],
    "unava": ["R53"],
    "fatigue": ["R53"],
    "weakness": ["R53"],
    "otoky": ["R60"],
    "swelling": ["R60"],
    "edema": ["R60"],
    "hubnutí": ["R63"],
    "hubnuti": ["R63"],
    "weight loss": ["R63"],
    "nechutenství": ["R63"],
    "loss of appetite": ["R63"],
    "krvácení": ["R58"],
    "krvaceni": ["R58"],
    "bleeding": ["R58"],
    "noční pocení": ["R61"],
    "nocni poceni": ["R61"],
    "night sweats": ["R61"],
    # --- Urologické / Urological ---
    "bolest při močení": ["R30", "N39"],
    "bolest pri moceni": ["R30", "N39"],
    "painful urination": ["R30", "N39"],
    "dysuria": ["R30", "N39"],
    "časté močení": ["R35"],
    "caste moceni": ["R35"],
    "frequent urination": ["R35"],
    "krev v moči": ["R31", "N39"],
    "krev v moci": ["R31", "N39"],
    "hematuria": ["R31"],
    # --- Kardiovaskulární / Cardiovascular ---
    "palpitace": ["R00"],
    "palpitations": ["R00"],
    "bušení srdce": ["R00"],
    "buseni srdce": ["R00"],
    "vysoký tlak": ["I10"],
    "vysoky tlak": ["I10"],
    "hypertension": ["I10"],
    "high blood pressure": ["I10"],
    "nízký tlak": ["I95"],
    "nizky tlak": ["I95"],
    "hypotension": ["I95"],
    # --- Oko / Eye ---
    "rozmazané vidění": ["H53"],
    "rozmazane videni": ["H53"],
    "blurred vision": ["H53"],
    "zarudnutí oka": ["H10"],
    "zarudnuti oka": ["H10"],
    "red eye": ["H10"],
    "conjunctivitis": ["H10"],
}

# Pre-built normalized lookup for fast exact matching.
_NORMALIZED_MAP: dict[str, list[str]] = {
    normalize_query(k): v for k, v in SYMPTOM_MKN_MAP.items()
}


def normalize_symptom(text: str) -> str:
    """Normalize a symptom string for dictionary lookup.

    Strips diacritics and lowercases.
    """
    return normalize_query(text)


def lookup_symptom(text: str) -> list[str] | None:
    """Exact lookup in the symptom map.

    Returns MKN-10 code prefixes or None.
    """
    key = normalize_symptom(text)
    return _NORMALIZED_MAP.get(key)


def fuzzy_lookup_symptom(
    text: str,
) -> list[tuple[str, list[str]]]:
    """Substring-based fuzzy lookup.

    Returns list of (matched_key, codes) where the
    normalized text is a substring of the key or vice versa.
    """
    needle = normalize_symptom(text)
    if len(needle) < 3:
        return []

    results: list[tuple[str, list[str]]] = []
    for key, codes in _NORMALIZED_MAP.items():
        if needle in key or key in needle:
            results.append((key, codes))
    return results
