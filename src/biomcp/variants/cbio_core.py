"""Shared cBioPortal API operations.

Consolidates duplicated gene ID lookup, molecular profile fetching,
and batch mutation fetching used across multiple cBioPortal clients.
"""

import logging
from typing import Any

from ..utils.cbio_http_adapter import CBioHTTPAdapter

logger = logging.getLogger(__name__)


class CBioPortalCoreClient:
    """Base class with shared cBioPortal API operations."""

    def __init__(self) -> None:
        self.http_adapter = CBioHTTPAdapter()

    async def get_gene_id(self, gene: str) -> int | None:
        """Get Entrez gene ID from gene symbol.

        Args:
            gene: Gene symbol (e.g., "BRAF")

        Returns:
            Entrez gene ID if found, None otherwise
        """
        gene_data, error = await self.http_adapter.get(
            f"/genes/{gene}",
            endpoint_key="cbioportal_genes",
            cache_ttl=3600,
        )

        if error or not gene_data:
            logger.warning(f"Failed to fetch gene info for {gene}")
            return None

        gene_id = gene_data.get("entrezGeneId")
        if not gene_id:
            logger.warning(
                f"No entrezGeneId in gene response for {gene}"
            )
            return None

        return gene_id

    async def get_mutation_profiles(
        self,
        params: dict[str, Any] | None = None,
        cache_ttl: int = 3600,
    ) -> list[dict[str, Any]]:
        """Fetch molecular profiles filtered by mutation type.

        Args:
            params: Additional query parameters
            cache_ttl: Cache time-to-live in seconds

        Returns:
            List of molecular profile dictionaries
        """
        request_params = params or {
            "molecularAlterationType": "MUTATION_EXTENDED"
        }
        profiles, error = await self.http_adapter.get(
            "/molecular-profiles",
            params=request_params,
            endpoint_key="cbioportal_molecular_profiles",
            cache_ttl=cache_ttl,
        )

        if error or not profiles:
            logger.warning("Failed to fetch molecular profiles")
            return []

        if not isinstance(profiles, list):
            return []

        return profiles

    async def fetch_mutations_batch(
        self,
        gene_id: int,
        profile_ids: list[str],
        cache_ttl: int = 1800,
    ) -> list[dict[str, Any]]:
        """Batch fetch mutations for a gene across profiles.

        Args:
            gene_id: Entrez gene ID
            profile_ids: List of molecular profile IDs
            cache_ttl: Cache time-to-live in seconds

        Returns:
            List of raw mutation records from cBioPortal
        """
        mutations_data, error = await self.http_adapter.post(
            "/mutations/fetch",
            data={
                "entrezGeneIds": [gene_id],
                "molecularProfileIds": profile_ids,
            },
            endpoint_key="cbioportal_mutations",
            cache_ttl=cache_ttl,
        )

        if error or not mutations_data:
            logger.warning(f"Failed to fetch mutations: {error}")
            return []

        if not isinstance(mutations_data, list):
            return []

        return mutations_data
