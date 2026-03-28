"""Czech medical synonym dictionary and symptom-cluster mapping.

Two complementary lookup mechanisms:

1. **CZ_MEDICAL_SYNONYMS** — maps common Czech colloquial
   medical terms (normalized, no diacritics) directly to
   ICD-10 codes.  ``lookup_synonym()`` provides the API.

2. **SYMPTOM_CLUSTER_MAP** — maps groups of co-occurring
   symptom keywords to ICD-10 codes with boost scores.
   When >=2 keywords from a cluster appear in the query,
   ``match_symptom_clusters()`` returns strong candidates.
"""

from czechmedmcp.czech.diacritics import normalize_query

# ---------------------------------------------------------
# Czech colloquial term → ICD-10 code dictionary
# Keys are normalized (lowercase, no diacritics).
# ---------------------------------------------------------
CZ_MEDICAL_SYNONYMS: dict[str, list[str]] = {
    # Metabolické
    "cukrovka": ["E11", "E10"],
    "diabetes": ["E11", "E10"],
    "vysoka hladina cukru": ["E11", "E10"],
    "vysoky tlak": ["I10"],
    "hypertenze": ["I10"],
    "krevni tlak": ["I10"],
    "vysoky krevni tlak": ["I10"],
    "cholesterol": ["E78"],
    "vysoka hladina tuku": ["E78"],
    "obezita": ["E66"],
    "tloustka": ["E66"],
    "dna": ["M10"],
    "pakostnice": ["M10"],
    # Kardiovaskulární
    "infarkt": ["I21"],
    "srdecni infarkt": ["I21"],
    "angina pectoris": ["I20"],
    "angina": ["I20", "J06"],
    "mrtvice": ["I64"],
    "mozkova prihoda": ["I64"],
    "iktus": ["I64"],
    "cevni mozkova prihoda": ["I63"],
    "fibrilace": ["I48"],
    "arytmie": ["I49"],
    "srdecni selhani": ["I50"],
    "krecove zily": ["I83"],
    "varixy": ["I83"],
    "embolie": ["I26"],
    "plicni embolie": ["I26"],
    # Respirační
    "astma": ["J45"],
    "zapal plic": ["J18"],
    "pneumonie": ["J18"],
    "bronchitida": ["J20", "J42"],
    "chripka": ["J11"],
    "flu": ["J11"],
    "nachladnuti": ["J06"],
    "ryma": ["J00"],
    "angina tonzil": ["J03"],
    "zanet mandli": ["J03"],
    "covid": ["U07.1"],
    # Onkologie
    "rakovina": ["C80"],
    "nadory": ["C80"],
    "rakovina prsu": ["C50"],
    "karcinom prsu": ["C50"],
    "rakovina plic": ["C34"],
    "rakovina tlustaho streva": ["C18"],
    "rakovina prostaty": ["C61"],
    "leukemie": ["C95"],
    "melanom": ["C43"],
    # GIT
    "zanet zaludku": ["K29"],
    "gastritida": ["K29"],
    "zaludecni vred": ["K25"],
    "vred": ["K25", "K26"],
    "prujem": ["K52", "A09"],
    "zapca": ["K59.0"],
    "zatvrdy": ["K59.0"],
    "hemeroidy": ["K64"],
    "zlucniky": ["K80"],
    "zlucove kameny": ["K80"],
    "zanet slepaho streva": ["K35"],
    "apendicitida": ["K35"],
    "crohn": ["K50"],
    "celiakie": ["K90.0"],
    # Neurologie
    "migrena": ["G43"],
    "bolest hlavy": ["G44", "R51"],
    "epilepsie": ["G40"],
    "parkinson": ["G20"],
    "alzheimer": ["G30"],
    "demence": ["F03"],
    "roztrousena skleroza": ["G35"],
    # Muskuloskeletální
    "bolest zad": ["M54"],
    "artritida": ["M13"],
    "revma": ["M06"],
    "revmatismus": ["M79"],
    "osteoporoza": ["M81"],
    "plotynka": ["M51"],
    "vyhrez plotynky": ["M51"],
    # Endokrinologie
    "stitna zlaza": ["E03", "E05"],
    "hypotyroza": ["E03"],
    "hypertyroza": ["E05"],
    # Psychiatrie
    "deprese": ["F32", "F33"],
    "uzkost": ["F41"],
    "uzkostna porucha": ["F41"],
    "nespavost": ["F51", "G47"],
    "insomnie": ["F51"],
    "schizofrenie": ["F20"],
    "porucha primu potravy": ["F50"],
    "anorexie": ["F50.0"],
    "bulimie": ["F50.2"],
    # Alergie / Imunologie
    "alergie": ["T78.4"],
    "senna ryma": ["J30.1"],
    "koprivka": ["L50"],
    "ekzem": ["L30"],
    "atopicky ekzem": ["L20"],
    "lupus": ["M32"],
    # Urologie / Nefrologie
    "ledvinove kameny": ["N20"],
    "zanet mocovych cest": ["N39.0"],
    "cystitis": ["N30"],
    "inkontinence": ["N39.3", "R32"],
    # ORL
    "zanet stredniho ucha": ["H66"],
    "otitida": ["H66"],
    "tinnitus": ["H93.1"],
    "huceni v usich": ["H93.1"],
    # Oční
    "sedy zakal": ["H25"],
    "katarakta": ["H25"],
    "zeleny zakal": ["H40"],
    "glaukom": ["H40"],
    # Dermatologie
    "lupeni": ["L40"],
    "psoriaza": ["L40"],
    "akne": ["L70"],
    "plisne": ["B35"],
    # Infekční
    "borellioza": ["A69.2"],
    "kliste": ["A69.2", "A84"],
    "tuberkuloza": ["A15"],
    "hepatitida": ["B19"],
    "zlatenka": ["B19", "K72"],
    "salmonela": ["A02"],
    # Jiné
    "anemie": ["D50", "D64"],
    "chudokrevnost": ["D50"],
    "zlomenina": ["T14.2"],
    "podvrtknuti": ["T14.3"],
    "popalniny": ["T30"],
    "otrava": ["T65"],
}

# Prevalence-based boost for common diagnosis codes.
# Higher = more common in population → ranked higher.
PREVALENCE_BOOST: dict[str, float] = {
    "E11": 10.0,   # T2DM — ~10x more common than T1DM
    "E10": 1.0,    # T1DM
    "I10": 8.0,    # Essential hypertension
    "J06": 7.0,    # Upper respiratory infection
    "J45": 5.0,    # Asthma
    "E66": 5.0,    # Obesity
    "F32": 4.0,    # Depressive episode
    "M54": 6.0,    # Dorsalgia (back pain)
    "I25": 4.0,    # Chronic ischaemic heart disease
    "E78": 5.0,    # Hyperlipidaemia
    "J20": 4.0,    # Acute bronchitis
    "K29": 3.0,    # Gastritis
    "I48": 3.0,    # Atrial fibrillation
    "I50": 3.0,    # Heart failure
    "G43": 3.0,    # Migraine
    "L40": 2.0,    # Psoriasis
    "N39": 4.0,    # UTI
    "I21": 3.0,    # Acute MI
    "J18": 3.0,    # Pneumonia
    "I64": 2.0,    # Stroke
    "C50": 2.0,    # Breast cancer
    "C34": 2.0,    # Lung cancer
    "C18": 2.0,    # Colon cancer
}


def lookup_synonym(query: str) -> list[str] | None:
    """Look up Czech colloquial term in synonym dictionary.

    Args:
        query: Search query (Czech or ASCII, any case).

    Returns:
        List of matching ICD-10 codes, or None if no match.
    """
    normalized = normalize_query(query)
    codes = CZ_MEDICAL_SYNONYMS.get(normalized)
    if codes is not None:
        return list(codes)
    return None


def get_prevalence_boost(code: str) -> float:
    """Return prevalence boost for a code (default 1.0)."""
    prefix = code.split(".")[0].upper()
    return PREVALENCE_BOOST.get(prefix, 1.0)


# Keys: tuple of normalized keywords (no diacritics).
# Values: list of (ICD-10 code, boost score).
# At least 2 keywords from a cluster must appear in the
# query for the cluster to match.
SYMPTOM_CLUSTER_MAP: dict[
    tuple[str, ...], list[tuple[str, float]]
] = {
    # --- Metabolické / Metabolic ---
    ("zizen", "moceni", "cukr"): [
        ("E11", 0.95),
        ("E10", 0.85),
    ],
    ("zizen", "moceni", "unava"): [
        ("E11", 0.90),
        ("E10", 0.80),
    ],
    ("zizen", "hubnuti", "moceni"): [
        ("E11", 0.90),
        ("E10", 0.85),
    ],
    ("thirst", "urination", "sugar"): [
        ("E11", 0.95),
        ("E10", 0.85),
    ],
    ("thirst", "urination", "fatigue"): [
        ("E11", 0.90),
        ("E10", 0.80),
    ],
    # --- Kardiovaskulární / Cardiovascular ---
    ("bolest", "hrud", "dusnost"): [
        ("I21", 0.90),
        ("I20", 0.85),
    ],
    ("chest", "pain", "breathlessness"): [
        ("I21", 0.90),
        ("I20", 0.85),
    ],
    ("bolest", "hrud", "poceni"): [
        ("I21", 0.90),
        ("I20", 0.80),
    ],
    ("buseni", "srdce", "dusnost"): [
        ("I49", 0.85),
        ("I48", 0.80),
    ],
    ("palpitace", "dusnost", "unava"): [
        ("I49", 0.85),
        ("I48", 0.80),
    ],
    # --- Respirační / Respiratory ---
    ("kasel", "horecka", "dusnost"): [
        ("J18", 0.90),
        ("J44", 0.80),
    ],
    ("cough", "fever", "dyspnea"): [
        ("J18", 0.90),
        ("J44", 0.80),
    ],
    ("kasel", "ryma", "horecka"): [
        ("J06", 0.90),
        ("J11", 0.80),
    ],
    # --- Neurologické / Neurological ---
    ("bolest", "hlavy", "zvraceni"): [
        ("G43", 0.90),
        ("G44", 0.80),
    ],
    ("headache", "nausea", "light"): [
        ("G43", 0.90),
        ("G44", 0.80),
    ],
    ("znecitliveni", "slabost", "rec"): [
        ("I63", 0.95),
        ("I64", 0.85),
    ],
    ("numbness", "weakness", "speech"): [
        ("I63", 0.95),
        ("I64", 0.85),
    ],
    # --- GIT / Gastrointestinal ---
    ("bolest", "bricha", "prujem"): [
        ("K52", 0.85),
        ("A09", 0.80),
    ],
    ("bolest", "bricha", "zvraceni"): [
        ("K29", 0.85),
        ("K25", 0.80),
    ],
    ("paleni", "zahy", "bolest"): [
        ("K21", 0.90),
        ("K25", 0.80),
    ],
    # --- Urologické / Urological ---
    ("bolest", "moceni", "horecka"): [
        ("N10", 0.90),
        ("N39", 0.85),
    ],
    ("painful", "urination", "fever"): [
        ("N10", 0.90),
        ("N39", 0.85),
    ],
    # --- Psychiatrické / Psychiatric ---
    ("uzkost", "nespavost", "neklid"): [
        ("F41", 0.90),
        ("F51", 0.80),
    ],
    ("deprese", "nespavost", "unava"): [
        ("F32", 0.90),
        ("F33", 0.85),
    ],
    # --- Štítná žláza / Thyroid ---
    ("unava", "prirustek", "zima"): [
        ("E03", 0.90),
        ("E02", 0.80),
    ],
    ("hubnuti", "poceni", "neklid"): [
        ("E05", 0.90),
    ],
}

# Oncology chapter prefixes used for demotion filter.
_ONCOLOGY_PREFIXES = ("C", "D0", "D1", "D2", "D3", "D4")

# Metabolic symptom keywords for demotion heuristic.
_METABOLIC_KEYWORDS = frozenset({
    "zizen", "cukr", "moceni", "thirst",
    "urination", "sugar", "diabetes",
    "glykemie", "inzulin", "insulin",
})


def match_symptom_clusters(
    query_normalized: str,
) -> list[tuple[str, float]]:
    """Match symptom clusters against a normalized query.

    Args:
        query_normalized: Lowercase, no-diacritics query.

    Returns:
        List of (ICD-10 code, boost score) for clusters
        where >=2 keywords appear in the query.
    """
    results: list[tuple[str, float]] = []
    seen_codes: set[str] = set()

    for keywords, codes in SYMPTOM_CLUSTER_MAP.items():
        matched = sum(
            1 for kw in keywords
            if kw in query_normalized
        )
        if matched >= 2:
            for code, score in codes:
                if code not in seen_codes:
                    results.append((code, score))
                    seen_codes.add(code)

    # Sort by score descending
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def is_oncology_code(code: str) -> bool:
    """Check if code belongs to oncology chapters C/D."""
    upper = code.upper().strip()
    return any(
        upper.startswith(p) for p in _ONCOLOGY_PREFIXES
    )


def has_metabolic_context(
    query_normalized: str,
) -> bool:
    """Check if query contains metabolic symptom keywords."""
    return any(
        kw in query_normalized
        for kw in _METABOLIC_KEYWORDS
    )
