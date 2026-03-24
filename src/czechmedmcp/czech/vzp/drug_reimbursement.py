"""VZP drug reimbursement and alternative comparison.

Uses SUKL reimbursement data + SUKL drug registry
for ATC-based alternative comparison.
Falls back to VZP static CSV dataset when SUKL API
returns no reimbursement data.
"""

import json
import logging

from czechmedmcp.czech.response import format_czech_response
from czechmedmcp.czech.vzp.data_loader import (
    get_vzp_reimbursement_for_code,
    load_vzp_reimbursement_data,
)
from czechmedmcp.czech.vzp.models import (
    AlternativeComparison,
    DrugAlternative,
    DrugReimbursement,
)

logger = logging.getLogger(__name__)


async def _get_vzp_drug_reimbursement(
    sukl_code: str,
) -> str:
    """Get VZP drug reimbursement details.

    Fetches reimbursement data from SUKL; when SUKL
    returns null, falls back to VZP static CSV dataset.

    Returns:
        Dual output JSON string.
    """
    detail = await _fetch_drug_detail(sukl_code)
    if not detail:
        return json.dumps(
            {"error": f"Drug not found: {sukl_code}"},
            ensure_ascii=False,
        )

    reimb = await _fetch_reimbursement(sukl_code)

    # Fallback: if SUKL returned no reimbursement data,
    # try VZP static CSV dataset
    if not _has_reimbursement_data(reimb):
        vzp_data = await _vzp_fallback(sukl_code)
        if vzp_data:
            reimb = vzp_data

    model = DrugReimbursement(
        sukl_code=sukl_code,
        name=detail.get("name", detail.get("nazev", "")),
        reimbursement_group=reimb.get("reimbursement_group"),
        max_price=reimb.get(
            "max_retail_price",
            reimb.get("max_price"),
        ),
        reimbursement_amount=reimb.get("reimbursement_amount"),
        patient_copay=reimb.get("patient_copay"),
        prescription_conditions=reimb.get("conditions"),
        valid_from=reimb.get("valid_from"),
    )

    md = _format_reimb_markdown(model)
    return format_czech_response(
        data=model.model_dump(),
        tool_name="get_vzp_reimbursement",
        markdown_template=md,
    )


async def _compare_alternatives(
    sukl_code: str,
) -> str:
    """Compare drug price alternatives in same ATC group.

    1. Get reference drug from SUKL (extract ATC).
    2. Search SUKL by ATC -> find alternatives.
    3. Get reimbursement for each -> sort by copay.

    Returns:
        Dual output JSON string.
    """
    detail = await _fetch_drug_detail(sukl_code)
    if not detail:
        return json.dumps(
            {"error": f"Drug not found: {sukl_code}"},
            ensure_ascii=False,
        )

    name = detail.get("name", detail.get("nazev", ""))
    atc = detail.get("atc_code", detail.get("ATCkod"))
    ref_reimb = await _fetch_reimbursement(sukl_code)
    ref_copay = ref_reimb.get("patient_copay")

    reimb_available = bool(ref_reimb)

    alts: list[DrugAlternative] = []
    if atc:
        alts = await _find_atc_alternatives(atc, sukl_code, ref_copay)

    model = AlternativeComparison(
        reference_sukl_code=sukl_code,
        reference_name=name,
        reference_copay=ref_copay,
        atc_code=atc,
        alternatives=alts,
        total_alternatives=len(alts),
    )

    md = _format_alt_markdown(model, reimb_available)
    return format_czech_response(
        data=model.model_dump(),
        tool_name="compare_alternatives",
        markdown_template=md,
    )


async def _fetch_drug_detail(
    sukl_code: str,
) -> dict | None:
    """Fetch drug detail from SUKL getter."""
    try:
        from czechmedmcp.czech.sukl.getter import (
            _sukl_drug_details,
        )

        raw = await _sukl_drug_details(sukl_code)
        data = json.loads(raw)
        if "error" in data:
            return None
        return data
    except Exception:
        logger.warning(
            "Failed to fetch drug detail for %s",
            sukl_code,
        )
        return None


async def _fetch_reimbursement(
    sukl_code: str,
) -> dict:
    """Fetch reimbursement from SUKL."""
    try:
        from czechmedmcp.czech.sukl.reimbursement import (
            _get_reimbursement,
        )

        raw = await _get_reimbursement(sukl_code)
        data = json.loads(raw)
        sc = data.get("structuredContent", data)
        return sc
    except Exception:
        logger.warning(
            "Failed to fetch reimbursement for %s",
            sukl_code,
        )
        return {}


async def _find_atc_alternatives(
    atc_code: str,
    reference_code: str,
    ref_copay: float | None,
) -> list[DrugAlternative]:
    """Search for ATC group alternatives."""
    try:
        from czechmedmcp.czech.sukl.search import (
            _sukl_drug_search,
        )

        raw = await _sukl_drug_search(atc_code, page=1, page_size=20)
        data = json.loads(raw)
    except Exception:
        logger.warning(
            "Failed to search ATC alternatives for %s",
            atc_code,
        )
        return []

    results = data.get("results", [])
    alts: list[DrugAlternative] = []

    for drug in results:
        code = drug.get("sukl_code", "")
        if code == reference_code:
            continue

        reimb = await _fetch_reimbursement(code)
        copay = reimb.get("patient_copay")
        savings = None
        if copay is not None and ref_copay is not None:
            savings = round(ref_copay - copay, 2)

        alts.append(
            DrugAlternative(
                sukl_code=code,
                name=drug.get("name", ""),
                patient_copay=copay,
                savings_vs_reference=savings,
            )
        )

    alts.sort(key=lambda a: a.patient_copay or 9999)
    return alts


def _has_reimbursement_data(reimb: dict) -> bool:
    """Check if reimbursement dict has actual data."""
    return any(
        reimb.get(k) is not None
        for k in (
            "reimbursement_group",
            "max_retail_price",
            "max_price",
            "reimbursement_amount",
            "patient_copay",
        )
    )


async def _vzp_fallback(
    sukl_code: str,
) -> dict | None:
    """Try VZP static CSV dataset as fallback."""
    try:
        await load_vzp_reimbursement_data()
        return get_vzp_reimbursement_for_code(sukl_code)
    except Exception:
        logger.warning("VZP fallback failed for %s", sukl_code)
        return None


def _format_reimb_markdown(
    r: DrugReimbursement,
) -> str:
    """Format drug reimbursement as Markdown."""
    lines = [
        f"## VZP Úhrada: {r.name}",
        "",
    ]

    has_data = any(
        v is not None
        for v in (
            r.reimbursement_group,
            r.max_price,
            r.reimbursement_amount,
            r.patient_copay,
        )
    )

    if not has_data:
        lines.append("Úhradová data nejsou dostupná pro tento SÚKL kód.")
        return "\n".join(lines)

    if r.reimbursement_group:
        lines.append(f"**Úhradová skupina**: {r.reimbursement_group}")
    if r.max_price is not None:
        lines.append(f"**Max. cena**: {r.max_price} CZK")
    if r.reimbursement_amount is not None:
        lines.append(f"**Úhrada**: {r.reimbursement_amount} CZK")
    if r.patient_copay is not None:
        lines.append(f"**Doplatek**: {r.patient_copay} CZK")
    if r.prescription_conditions:
        lines.append(f"**Podmínky**: {r.prescription_conditions}")
    return "\n".join(lines)


def _format_alt_markdown(
    r: AlternativeComparison,
    reimb_available: bool = True,
) -> str:
    """Format alternative comparison as Markdown."""
    lines = [
        f"## Cenové alternativy: {r.reference_name}",
        "",
    ]
    if r.atc_code:
        lines.append(f"**ATC skupina**: {r.atc_code}")
    if r.reference_copay is not None:
        lines.append(f"**Referenční doplatek**: {r.reference_copay} CZK")
    elif not reimb_available:
        lines.append(
            "**Referenční doplatek**: N/A (údaje o úhradě nedostupné)"
        )

    if r.alternatives:
        lines.extend([
            "",
            "| Přípravek | Doplatek | Úspora |",
            "|-----------|----------|--------|",
        ])
        for a in r.alternatives:
            copay = (
                f"{a.patient_copay} CZK"
                if a.patient_copay is not None
                else "N/A"
            )
            savings = (
                f"{a.savings_vs_reference} CZK"
                if a.savings_vs_reference is not None
                else "N/A"
            )
            lines.append(f"| {a.name} | {copay} | {savings} |")
    else:
        lines.append("\n*Žádné alternativy nalezeny.*")

    return "\n".join(lines)
