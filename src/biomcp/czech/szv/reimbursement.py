"""SZV procedure reimbursement calculation.

Calculates CZK reimbursement based on procedure
point value and insurance company rate.
"""

import json
import logging

from biomcp.constants import INSURANCE_RATE_TABLE
from biomcp.czech.response import format_czech_response
from biomcp.czech.szv.models import (
    ReimbursementCalculation,
)
from biomcp.czech.szv.search import _szv_get

logger = logging.getLogger(__name__)

_INSURANCE_NAMES: dict[str, str] = {
    "111": "VZP",
    "201": "VoZP",
    "205": "ČPZP",
    "207": "OZP",
    "209": "ZPŠ",
    "211": "ZPMV",
    "213": "RBP",
}


async def _calculate_reimbursement(
    procedure_code: str,
    insurance_code: str = "111",
    count: int = 1,
) -> str:
    """Calculate CZK reimbursement for a procedure.

    Args:
        procedure_code: 5-digit SZV procedure code.
        insurance_code: Insurance company code.
        count: Number of procedures.

    Returns:
        Dual output JSON string.
    """
    rate = INSURANCE_RATE_TABLE.get(insurance_code)
    if rate is None:
        return json.dumps(
            {
                "error": (
                    f"Unknown insurance code: "
                    f"{insurance_code}"
                ),
            },
            ensure_ascii=False,
        )

    procedure_raw = await _szv_get(procedure_code)
    procedure = json.loads(procedure_raw)
    if "error" in procedure:
        return json.dumps(procedure, ensure_ascii=False)

    points = procedure.get("point_value")
    if points is None:
        return json.dumps(
            {
                "error": (
                    f"No point value for "
                    f"{procedure_code}"
                ),
            },
            ensure_ascii=False,
        )

    points = int(points)
    unit_price = round(points * rate, 2)
    total = round(unit_price * count, 2)

    model = ReimbursementCalculation(
        procedure_code=procedure_code,
        procedure_name=procedure.get("name", ""),
        point_value=points,
        insurance_code=insurance_code,
        insurance_name=_INSURANCE_NAMES.get(
            insurance_code, insurance_code
        ),
        rate_per_point=rate,
        count=count,
        unit_price_czk=unit_price,
        total_czk=total,
    )

    md = _format_markdown(model)
    return format_czech_response(
        data=model.model_dump(),
        tool_name="calculate_reimbursement",
        markdown_template=md,
    )


def _format_markdown(
    r: ReimbursementCalculation,
) -> str:
    """Format reimbursement as Markdown."""
    lines = [
        f"## Kalkulace: {r.procedure_code}"
        f" — {r.procedure_name}",
        "",
        f"**Body**: {r.point_value}",
        f"**Pojišťovna**: {r.insurance_name}"
        f" ({r.insurance_code})",
        f"**Sazba**: {r.rate_per_point} CZK/bod",
        f"**Cena za výkon**: {r.unit_price_czk} CZK",
    ]
    if r.count > 1:
        lines.append(
            f"**Celkem ({r.count}x)**: "
            f"{r.total_czk} CZK"
        )
    return "\n".join(lines)
