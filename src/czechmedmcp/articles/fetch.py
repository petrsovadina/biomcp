import json
import logging
import re
from ssl import TLSVersion
from typing import Annotated, Any

import httpx
from pydantic import BaseModel, Field, computed_field

from .. import http_client, render
from ..constants import (
    CACHE_TTL_MONTH,
    NCBI_PMC_CONVERTER_URL,
    PUBTATOR3_FULLTEXT_URL,
)
from ..http_client import (
    RequestError,
    cache_response,
    generate_cache_key,
    get_cached_response,
)

logger = logging.getLogger(__name__)


class PassageInfo(BaseModel):
    section_type: str | None = Field(
        None,
        description="Type of the section.",
    )
    passage_type: str | None = Field(
        None,
        alias="type",
        description="Type of the passage.",
    )


class Passage(BaseModel):
    info: PassageInfo | None = Field(
        None,
        alias="infons",
    )
    text: str | None = None

    @property
    def section_type(self) -> str:
        section_type = None
        if self.info is not None:
            section_type = self.info.section_type or self.info.passage_type
        section_type = section_type or "UNKNOWN"
        return section_type.upper()

    @property
    def is_title(self) -> bool:
        return self.section_type == "TITLE"

    @property
    def is_abstract(self) -> bool:
        return self.section_type == "ABSTRACT"

    @property
    def is_text(self) -> bool:
        return self.section_type in {
            "INTRO",
            "RESULTS",
            "METHODS",
            "DISCUSS",
            "CONCL",
            "FIG",
            "TABLE",
        }


class Article(BaseModel):
    pmid: int | None = Field(
        None,
        description="PubMed ID of the reference article.",
    )
    pmcid: str | None = Field(
        None,
        description="PubMed Central ID of the reference article.",
    )
    date: str | None = Field(
        None,
        description="Date of the reference article's publication.",
    )
    journal: str | None = Field(
        None,
        description="Journal name.",
    )
    authors: list[str] | None = Field(
        None,
        description="List of authors.",
    )
    passages: list[Passage] = Field(
        ...,
        alias="passages",
        description="List of passages in the reference article.",
        exclude=True,
    )

    @computed_field
    def title(self) -> str:
        lines = []
        for passage in filter(lambda p: p.is_title, self.passages):
            if passage.text:
                lines.append(passage.text)
        return " ... ".join(lines) or f"Article: {self.pmid}"

    @computed_field
    def abstract(self) -> str:
        lines = []
        for passage in filter(lambda p: p.is_abstract, self.passages):
            if passage.text:
                lines.append(passage.text)
        return "\n\n".join(lines) or f"Article: {self.pmid}"

    @computed_field
    def full_text(self) -> str:
        lines = []
        for passage in filter(lambda p: p.is_text, self.passages):
            if passage.text:
                lines.append(passage.text)
        return "\n\n".join(lines) or ""

    @computed_field
    def pubmed_url(self) -> str | None:
        url = None
        if self.pmid:
            url = f"https://pubmed.ncbi.nlm.nih.gov/{self.pmid}/"
        return url

    @computed_field
    def pmc_url(self) -> str | None:
        """Generates the PMC URL if PMCID exists."""
        url = None
        if self.pmcid:
            url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{self.pmcid}/"
        return url


class FetchArticlesResponse(BaseModel):
    articles: list[Article] = Field(
        ...,
        alias="PubTator3",
        description="List of full texts Articles retrieved from PubTator3.",
    )

    def get_abstract(self, pmid: int | None) -> str | None:
        for article in self.articles:
            if pmid and article.pmid == pmid:
                return str(article.abstract)
        return None


async def call_pubtator_api(
    pmids: list[int],
    full: bool,
) -> tuple[FetchArticlesResponse | None, RequestError | None]:
    """Fetch the text of a list of PubMed IDs."""

    request = {
        "pmids": ",".join(str(pmid) for pmid in pmids),
        "full": str(full).lower(),
    }

    response, error = await http_client.request_api(
        url=PUBTATOR3_FULLTEXT_URL,
        request=request,
        response_model_type=FetchArticlesResponse,
        tls_version=TLSVersion.TLSv1_2,
        domain="pubmed",
    )
    return response, error


async def _fetch_abstract_efetch(
    pmid: int,
) -> str | None:
    """Fetch abstract from PubMed E-utilities as fallback."""
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": str(pmid),
        "rettype": "abstract",
        "retmode": "text",
    }
    cache_key = generate_cache_key("GET", url, params)
    cached = get_cached_response(cache_key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            text = resp.text.strip()
            if text and len(text) > 50:
                cache_response(cache_key, text, CACHE_TTL_MONTH)
                return text
    except Exception:
        logger.debug(
            "E-utilities abstract fetch failed for %s",
            pmid,
        )
    return None


async def fetch_articles(
    pmids: list[int],
    full: bool,
    output_json: bool = False,
) -> str:
    """Fetch the text of a list of PubMed IDs."""

    response, error = await call_pubtator_api(pmids, full)

    # PubTator API returns full text even when full=False
    exclude_fields = {"full_text"} if not full else set()

    # noinspection DuplicatedCode
    if error:
        data: list[dict[str, Any]] = [
            {"error": f"Error {error.code}: {error.message}"}
        ]
    else:
        data = [
            article.model_dump(
                mode="json",
                exclude_none=True,
                exclude=exclude_fields,
            )
            for article in (response.articles if response else [])
        ]

    # Patch articles that have placeholder abstracts
    for item in data:
        abstract = item.get("abstract", "")
        pmid_val = item.get("pmid")
        if pmid_val and abstract.startswith("Article: "):
            real_abstract = await _fetch_abstract_efetch(pmid_val)
            if real_abstract:
                item["abstract"] = real_abstract

    if data and not output_json:
        return render.to_markdown(data)
    else:
        return json.dumps(data, indent=2)


def is_doi(identifier: str) -> bool:
    """Check if the identifier is a DOI."""
    # DOI pattern: starts with 10. followed by numbers/slash/alphanumeric
    doi_pattern = r"^10\.\d{4,9}/[\-._;()/:\w]+$"
    return bool(re.match(doi_pattern, str(identifier)))


def is_pmid(identifier: str) -> bool:
    """Check if the identifier is a PubMed ID."""
    # PMID is a numeric string
    return str(identifier).isdigit()


def is_pmc_id(identifier: str) -> bool:
    """Check if the identifier is a PMC ID (e.g., PMC11193658)."""
    return bool(re.match(r"^PMC\d{7,8}$", str(identifier), re.IGNORECASE))


async def _convert_pmc_to_pmid(pmc_id: str) -> int | None:
    """Convert a PMC ID to a PMID via NCBI ID Converter API.

    Results are cached for CACHE_TTL_MONTH to avoid repeated
    API calls for the same PMC ID.

    Returns the integer PMID, or None if conversion fails.
    """
    cache_key = generate_cache_key(
        "GET", NCBI_PMC_CONVERTER_URL, {"ids": pmc_id}
    )
    cached = get_cached_response(cache_key)
    if cached is not None:
        try:
            return int(cached)
        except (ValueError, TypeError):
            pass

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                NCBI_PMC_CONVERTER_URL,
                params={
                    "ids": pmc_id,
                    "format": "json",
                    "tool": "czechmedmcp",
                },
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        logger.warning(
            "PMC ID conversion failed for %s", pmc_id, exc_info=True
        )
        return None

    records = data.get("records", [])
    if not records:
        return None

    pmid_raw = records[0].get("pmid")
    if pmid_raw is None:
        return None

    try:
        pmid = int(pmid_raw)
    except (ValueError, TypeError):
        return None

    cache_response(cache_key, str(pmid), CACHE_TTL_MONTH)
    return pmid


async def _article_details(  # noqa: C901
    call_benefit: Annotated[
        str,
        "Define and summarize why this function is being called and the intended benefit",
    ],
    pmid,
) -> str:
    """
    Retrieves details for a single article given its identifier.

    Parameters:
    - call_benefit: Define and summarize why this function is being called and the intended benefit
    - pmid: An article identifier - either a PubMed ID (e.g., 34397683), PMC ID (e.g., PMC11193658), or DOI (e.g., 10.1101/2024.01.20.23288905)

    Process:
    - For PMIDs: Calls the PubTator3 API to fetch the article's title, abstract, and full text (if available)
    - For PMC IDs: Converts to PMID via NCBI ID Converter, then uses PubTator3 flow
    - For DOIs: Calls Europe PMC API to fetch preprint details

    Output: A JSON formatted string containing the retrieved article content.
    """
    identifier = str(pmid)

    # Check if it's a DOI (Europe PMC preprint)
    if is_doi(identifier):
        from .preprints import fetch_europe_pmc_article

        try:
            return await fetch_europe_pmc_article(identifier, output_json=True)
        except Exception as exc:
            logger.error(
                "Europe PMC fetch failed for DOI %s: %s",
                identifier,
                exc,
            )
            return json.dumps(
                [
                    {
                        "error": (
                            f"Failed to fetch article for DOI"
                            f" {identifier}."
                            f" The Europe PMC service may be"
                            f" temporarily unavailable."
                        )
                    }
                ],
                indent=2,
                ensure_ascii=False,
            )

    # Check if it's a PMC ID — convert to PMID first
    if is_pmc_id(identifier):
        converted = await _convert_pmc_to_pmid(identifier)
        if converted is None:
            return json.dumps(
                [
                    {
                        "error": (
                            f"Could not convert {identifier}"
                            f" to a PMID. The PMC ID may be"
                            f" invalid or the NCBI converter"
                            f" service is unavailable."
                        )
                    }
                ],
                indent=2,
                ensure_ascii=False,
            )
        identifier = str(converted)
        # Fall through to PMID handling below

    # Check if it's a PMID (PubMed article)
    if is_pmid(identifier):
        try:
            result = await fetch_articles(
                [int(identifier)], full=True, output_json=True
            )
        except Exception as exc:
            logger.error(
                "PubTator3 fetch failed for PMID %s: %s",
                identifier,
                exc,
            )
            result = None

        # If PubTator3 succeeded, return the result
        if result is not None:
            try:
                parsed = json.loads(result)
                if parsed and not any("error" in item for item in parsed):
                    return result
            except (json.JSONDecodeError, TypeError):
                return result

        # Fallback: try Europe PMC by PMID
        try:
            from .preprints import fetch_europe_pmc_article

            fallback = await fetch_europe_pmc_article(
                identifier, output_json=True
            )
            parsed_fb = json.loads(fallback)
            if parsed_fb and not any("error" in item for item in parsed_fb):
                return fallback
        except Exception:
            logger.debug(
                "Europe PMC fallback also failed for %s",
                identifier,
                exc_info=True,
            )

        # Return original PubTator3 result (may contain error)
        if result is not None:
            return result

        return json.dumps(
            [
                {
                    "error": (
                        f"Failed to fetch article for PMID"
                        f" {identifier}. Both PubTator3 and"
                        f" Europe PMC services are"
                        f" unavailable."
                    )
                }
            ],
            indent=2,
            ensure_ascii=False,
        )

    # Unknown identifier format
    return json.dumps(
        [
            {
                "error": (
                    f"Invalid identifier format:"
                    f" {pmid!s}. Expected a PMID"
                    f" (numeric, e.g. 34397683),"
                    f" PMC ID (e.g. PMC11193658),"
                    f" or DOI (e.g."
                    f" 10.1101/2024.01.20.23288905)."
                )
            }
        ],
        indent=2,
        ensure_ascii=False,
    )
