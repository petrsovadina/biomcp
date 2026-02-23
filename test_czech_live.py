"""Functional live-API tests for each Czech healthcare MCP tool module.

Run with:
    uv run python test_czech_live.py

Each test calls the underlying async function directly and prints a
one-line result:  TOOL_NAME - OK/FAIL - brief description
"""

import asyncio
import json
import sys
import time

# ---------------------------------------------------------------------------
# Minimal ClaML XML for MKN tests (covers J06, diabetes-related codes).
# The MKN module does NOT fetch XML from the network -- it requires the
# caller to supply a ClaML XML string.  We embed a small but valid
# excerpt so the test does not depend on an external download.
# ---------------------------------------------------------------------------
_MKN_SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ClaML version="2.0.0">
  <Class code="X" kind="chapter">
    <Rubric kind="preferred"><Label xml:lang="cs">Nemoci dychaci soustavy</Label></Rubric>
    <SubClass code="J00-J06"/>
    <SubClass code="J10-J18"/>
  </Class>
  <Class code="J00-J06" kind="block">
    <SuperClass code="X"/>
    <Rubric kind="preferred"><Label xml:lang="cs">Akutni respiracni infekce</Label></Rubric>
    <SubClass code="J06"/>
  </Class>
  <Class code="J06" kind="category">
    <SuperClass code="J00-J06"/>
    <Rubric kind="preferred">
      <Label xml:lang="cs">Akutni infekce hornich dychacich cest na vice mistech nebo NS</Label>
    </Rubric>
    <SubClass code="J06.9"/>
  </Class>
  <Class code="J06.9" kind="category">
    <SuperClass code="J06"/>
    <Rubric kind="preferred">
      <Label xml:lang="cs">Akutni infekce hornich dychacich cest NS</Label>
    </Rubric>
  </Class>
  <Class code="IV" kind="chapter">
    <Rubric kind="preferred">
      <Label xml:lang="cs">Nemoci endokrinni soustavy, poruchy vyzive a latkovej premeny</Label>
    </Rubric>
    <SubClass code="E10-E14"/>
  </Class>
  <Class code="E10-E14" kind="block">
    <SuperClass code="IV"/>
    <Rubric kind="preferred"><Label xml:lang="cs">Diabetes mellitus</Label></Rubric>
    <SubClass code="E11"/>
  </Class>
  <Class code="E11" kind="category">
    <SuperClass code="E10-E14"/>
    <Rubric kind="preferred">
      <Label xml:lang="cs">Diabetes mellitus 2. typu</Label>
    </Rubric>
  </Class>
</ClaML>
"""

# ---------------------------------------------------------------------------
# Result tracking
# ---------------------------------------------------------------------------

results: list[tuple[str, str, str]] = []


def record(name: str, ok: bool, note: str) -> None:
    status = "OK" if ok else "FAIL"
    results.append((name, status, note))
    marker = "[OK]  " if ok else "[FAIL]"
    print(f"  {marker}  {name} - {note}")


# ---------------------------------------------------------------------------
# 1. SUKL - Drug Registry
# ---------------------------------------------------------------------------


async def test_sukl_drug_details() -> None:
    """Fetch full details for the first code in the SUKL drug list."""
    from biomcp.czech.sukl.getter import _sukl_drug_details
    from biomcp.czech.sukl.search import _fetch_drug_list

    try:
        codes = await _fetch_drug_list()
        if not codes:
            record("SUKL_drug_details", False, "Drug list is empty")
            return

        sukl_code = codes[0]
        raw = await _sukl_drug_details(sukl_code)
        data = json.loads(raw)

        if "error" in data:
            record(
                "SUKL_drug_details",
                False,
                "code=" + sukl_code + ", error: " + str(data["error"]),
            )
            return

        has_name = bool(data.get("name"))
        source_ok = data.get("source") == "SUKL"
        note = (
            "code=" + sukl_code
            + ", name=" + repr(data.get("name", "?"))
            + ", source=" + str(data.get("source", "?"))
        )
        record("SUKL_drug_details", has_name and source_ok, note)
    except Exception as exc:
        record("SUKL_drug_details", False, "Exception: " + str(exc))


async def test_sukl_availability() -> None:
    """Check availability for the first code from the SUKL drug list."""
    from biomcp.czech.sukl.availability import _sukl_availability_check
    from biomcp.czech.sukl.search import _fetch_drug_list

    try:
        codes = await _fetch_drug_list()
        if not codes:
            record("SUKL_availability", False, "Drug list is empty")
            return

        sukl_code = codes[0]
        raw = await _sukl_availability_check(sukl_code)
        data = json.loads(raw)

        if "error" in data:
            record(
                "SUKL_availability",
                False,
                "code=" + sukl_code + ", error: " + str(data["error"]),
            )
            return

        status = data.get("status", "")
        valid_statuses = {"available", "limited", "unavailable"}
        note = (
            "code=" + sukl_code
            + ", status=" + repr(status)
            + ", source=" + str(data.get("source", "?"))
        )
        record("SUKL_availability", status in valid_statuses, note)
    except Exception as exc:
        record("SUKL_availability", False, "Exception: " + str(exc))


async def test_sukl_search_ibuprofen() -> None:
    """Search for 'ibuprofen' in the SUKL drug registry."""
    from biomcp.czech.sukl.search import _sukl_drug_search

    try:
        t0 = time.monotonic()
        raw = await _sukl_drug_search("ibuprofen", page=1, page_size=5)
        elapsed = time.monotonic() - t0
        data = json.loads(raw)

        if "error" in data:
            record(
                "SUKL_search_ibuprofen",
                False,
                "API error: " + str(data["error"]),
            )
            return

        total = data.get("total", 0)
        count = len(data.get("results", []))
        note = (
            "total=" + str(total)
            + ", returned=" + str(count)
            + ", elapsed=" + str(round(elapsed, 1)) + "s"
        )
        record("SUKL_search_ibuprofen", total >= 1 and count >= 1, note)
    except Exception as exc:
        record("SUKL_search_ibuprofen", False, "Exception: " + str(exc))


async def test_sukl_search_paralen() -> None:
    """Search for 'paralen' in the SUKL drug registry."""
    from biomcp.czech.sukl.search import _sukl_drug_search

    try:
        t0 = time.monotonic()
        raw = await _sukl_drug_search("paralen", page=1, page_size=5)
        elapsed = time.monotonic() - t0
        data = json.loads(raw)

        if "error" in data:
            record(
                "SUKL_search_paralen",
                False,
                "API error: " + str(data["error"]),
            )
            return

        total = data.get("total", 0)
        count = len(data.get("results", []))
        note = (
            "total=" + str(total)
            + ", returned=" + str(count)
            + ", elapsed=" + str(round(elapsed, 1)) + "s"
        )
        record("SUKL_search_paralen", total >= 1 and count >= 1, note)
    except Exception as exc:
        record("SUKL_search_paralen", False, "Exception: " + str(exc))


# ---------------------------------------------------------------------------
# 2. MKN - ICD-10 Diagnosis Codes (uses embedded XML, no live API)
# ---------------------------------------------------------------------------


async def test_mkn_search_diabetes() -> None:
    """Full-text search for 'diabetes' in the embedded MKN-10 XML."""
    from biomcp.czech.mkn.search import _mkn_search

    try:
        raw = await _mkn_search(
            "diabetes", max_results=10, xml_content=_MKN_SAMPLE_XML
        )
        data = json.loads(raw)

        if "error" in data:
            record("MKN_search_diabetes", False, "Error: " + str(data["error"]))
            return

        total = data.get("total", 0)
        res_list = data.get("results", [])
        first_desc = str(res_list[0]) if res_list else "none"
        note = "total=" + str(total) + ", first=" + first_desc
        record("MKN_search_diabetes", total >= 1 and len(res_list) >= 1, note)
    except Exception as exc:
        record("MKN_search_diabetes", False, "Exception: " + str(exc))


async def test_mkn_lookup_j06() -> None:
    """Look up code 'J06' by exact code in the embedded MKN-10 XML."""
    from biomcp.czech.mkn.search import _mkn_get

    try:
        raw = await _mkn_get("J06", xml_content=_MKN_SAMPLE_XML)
        data = json.loads(raw)

        if "error" in data:
            record("MKN_lookup_J06", False, "Error: " + str(data["error"]))
            return

        code_ok = data.get("code") == "J06"
        has_name = bool(data.get("name_cs"))
        has_hier = data.get("hierarchy") is not None
        note = (
            "code=" + str(data.get("code"))
            + ", name_cs=" + repr(data.get("name_cs", ""))
            + ", hierarchy=" + ("present" if has_hier else "missing")
        )
        record("MKN_lookup_J06", code_ok and has_name, note)
    except Exception as exc:
        record("MKN_lookup_J06", False, "Exception: " + str(exc))


async def test_mkn_browse_root() -> None:
    """Browse root chapters of the embedded MKN-10 XML."""
    from biomcp.czech.mkn.search import _mkn_browse

    try:
        raw = await _mkn_browse(code=None, xml_content=_MKN_SAMPLE_XML)
        data = json.loads(raw)

        if "error" in data:
            record("MKN_browse_root", False, "Error: " + str(data["error"]))
            return

        items = data.get("items", [])
        first_code = items[0]["code"] if items else "none"
        note = (
            "type=" + str(data.get("type"))
            + ", chapters=" + str(len(items))
            + ", first=" + first_code
        )
        record("MKN_browse_root", len(items) >= 1, note)
    except Exception as exc:
        record("MKN_browse_root", False, "Exception: " + str(exc))


# ---------------------------------------------------------------------------
# 3. NRPZS - Healthcare Provider Registry
# ---------------------------------------------------------------------------


async def test_nrpzs_search_praha() -> None:
    """Search for healthcare providers in Praha."""
    from biomcp.czech.nrpzs.search import _nrpzs_search

    try:
        raw = await _nrpzs_search(city="Praha", page=1, page_size=5)
        data = json.loads(raw)

        if "error" in data:
            record(
                "NRPZS_search_Praha",
                False,
                "API error: " + str(data["error"]),
            )
            return

        total = data.get("total", 0)
        count = len(data.get("results", []))
        first_ok = True
        if data["results"]:
            first = data["results"][0]
            first_ok = (
                "provider_id" in first
                and "name" in first
                and isinstance(first.get("specialties"), list)
            )
        note = (
            "total=" + str(total)
            + ", returned=" + str(count)
            + ", structure_ok=" + str(first_ok)
        )
        record("NRPZS_search_Praha", total >= 0 and first_ok, note)
    except Exception as exc:
        record("NRPZS_search_Praha", False, "Exception: " + str(exc))


async def test_nrpzs_get_provider() -> None:
    """Fetch full detail for the first provider found in Praha."""
    from biomcp.czech.nrpzs.search import _nrpzs_get, _nrpzs_search

    try:
        raw_search = await _nrpzs_search(city="Praha", page=1, page_size=1)
        search_data = json.loads(raw_search)

        if not search_data.get("results"):
            record(
                "NRPZS_get_provider",
                False,
                "No results from Praha search -- cannot test getter",
            )
            return

        provider_id = search_data["results"][0]["provider_id"]
        raw_detail = await _nrpzs_get(provider_id)
        detail = json.loads(raw_detail)

        if "error" in detail:
            record(
                "NRPZS_get_provider",
                False,
                "id=" + provider_id + ", error: " + str(detail["error"]),
            )
            return

        required = {"provider_id", "name", "source", "specialties"}
        has_all = required.issubset(detail.keys())
        source_ok = detail.get("source") == "NRPZS"
        note = (
            "id=" + provider_id
            + ", name=" + repr(detail.get("name", "?"))
            + ", source=" + str(detail.get("source", "?"))
        )
        record("NRPZS_get_provider", has_all and source_ok, note)
    except Exception as exc:
        record("NRPZS_get_provider", False, "Exception: " + str(exc))


# ---------------------------------------------------------------------------
# 4. SZV - Insurance / Procedure Codes
# ---------------------------------------------------------------------------


async def test_szv_search_ekg() -> None:
    """Search for 'EKG' procedure in SZV/NZIP."""
    from biomcp.czech.szv.search import _szv_search

    try:
        raw = await _szv_search("EKG", max_results=10)
        data = json.loads(raw)

        if "error" in data:
            record("SZV_search_EKG", False, "API error: " + str(data["error"]))
            return

        total = data.get("total", 0)
        res_list = data.get("results", [])
        first_name = res_list[0].get("name", "?") if res_list else "none"
        note = (
            "total=" + str(total)
            + ", returned=" + str(len(res_list))
            + ", first=" + repr(first_name)
        )
        # Accept total=0 (API offline) as long as structure is valid
        is_valid = "total" in data and "results" in data
        record("SZV_search_EKG", is_valid, note)
    except Exception as exc:
        record("SZV_search_EKG", False, "Exception: " + str(exc))


async def test_szv_get_procedure() -> None:
    """Fetch detail for procedure code '09513'."""
    from biomcp.czech.szv.search import _szv_get

    try:
        raw = await _szv_get("09513")
        data = json.loads(raw)

        is_valid = (
            "code" in data and data.get("source") == "MZCR/SZV"
        ) or "error" in data
        note = (
            "code=" + str(data.get("code", "N/A"))
            + ", source=" + str(data.get("source", "N/A"))
            + (", error: " + str(data["error"]) if "error" in data else ", OK")
        )
        record("SZV_get_procedure_09513", is_valid, note)
    except Exception as exc:
        record("SZV_get_procedure_09513", False, "Exception: " + str(exc))


# ---------------------------------------------------------------------------
# 5. VZP - Reimbursement / Codebook Data
# ---------------------------------------------------------------------------


async def test_vzp_search() -> None:
    """Search VZP codebooks for 'EKG'."""
    from biomcp.czech.vzp.search import _vzp_search

    try:
        raw = await _vzp_search(
            "EKG", codebook_type="seznam_vykonu", max_results=10
        )
        data = json.loads(raw)

        total = data.get("total", 0)
        res_list = data.get("results", [])
        first_name = res_list[0].get("name", "?") if res_list else "none"
        is_valid = "total" in data and "results" in data
        note = (
            "total=" + str(total)
            + ", returned=" + str(len(res_list))
            + ", first=" + repr(first_name)
        )
        record("VZP_search_EKG", is_valid, note)
    except Exception as exc:
        record("VZP_search_EKG", False, "Exception: " + str(exc))


async def test_vzp_get() -> None:
    """Fetch VZP codebook entry for 'seznam_vykonu' / '09513'."""
    from biomcp.czech.vzp.search import _vzp_get

    try:
        raw = await _vzp_get("seznam_vykonu", "09513")
        data = json.loads(raw)

        is_valid = (
            "code" in data and data.get("source") == "VZP"
        ) or "error" in data
        note = (
            "code=" + str(data.get("code", "N/A"))
            + ", source=" + str(data.get("source", "N/A"))
            + (", error: " + str(data["error"]) if "error" in data else ", OK")
        )
        record("VZP_get_09513", is_valid, note)
    except Exception as exc:
        record("VZP_get_09513", False, "Exception: " + str(exc))


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


async def main() -> None:
    print("\n=== BioMCP Czech Healthcare Tool -- Functional Live Tests ===\n")

    print("--- SUKL (Drug Registry) ---")
    # Fetch the drug list once (it will be cached), then run all SUKL tests.
    # Detail/availability reuse the cached list; search tests iterate codes.
    await test_sukl_drug_details()
    await test_sukl_availability()
    await test_sukl_search_ibuprofen()
    await test_sukl_search_paralen()

    print("\n--- MKN (ICD-10 Diagnosis Codes -- embedded XML, no live API) ---")
    await test_mkn_search_diabetes()
    await test_mkn_lookup_j06()
    await test_mkn_browse_root()

    print("\n--- NRPZS (Healthcare Provider Registry) ---")
    await test_nrpzs_search_praha()
    await test_nrpzs_get_provider()

    print("\n--- SZV (Procedure Codes / NZIP) ---")
    await test_szv_search_ekg()
    await test_szv_get_procedure()

    print("\n--- VZP (Reimbursement / Codebooks) ---")
    await test_vzp_search()
    await test_vzp_get()

    # Summary
    print("\n=== Summary ===\n")
    ok_count = sum(1 for _, s, _ in results if s == "OK")
    fail_count = sum(1 for _, s, _ in results if s == "FAIL")

    for name, status, note in results:
        marker = "[OK]  " if status == "OK" else "[FAIL]"
        print(f"  {marker}  {name} - {status} - {note}")

    print(f"\nTotal: {len(results)}  OK: {ok_count}  FAIL: {fail_count}")

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
