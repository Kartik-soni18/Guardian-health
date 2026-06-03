"""
PubMedService — NCBI E-utilities API integration for medical literature search.

Features:
- NCBI E-utilities with proper rate limiting
- API key support (10 req/s with key, 3 req/s without)
- cachetools.TTLCache for in-memory caching
- FastAPI BackgroundTasks-compatible (can run inline or background)
- XML parsing for abstracts
"""


import logging
import os
import time
import xml.etree.ElementTree as ET
from typing import Any

import httpx
from cachetools import TTLCache

logger = logging.getLogger("guardian.pubmed")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "")
NCBI_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PUBMED_CACHE_SIZE = 256
PUBMED_CACHE_TTL = 3600  # 1 hour

# Rate limiting: 10 req/s with key, 3 req/s without
RATE_LIMIT_REQUESTS = 10 if NCBI_API_KEY else 3
RATE_LIMIT_WINDOW = 1.0  # seconds

# ---------------------------------------------------------------------------
# In-memory cache
# ---------------------------------------------------------------------------
_pubmed_cache: TTLCache = TTLCache(maxsize=PUBMED_CACHE_SIZE, ttl=PUBMED_CACHE_TTL)

# ---------------------------------------------------------------------------
# Rate limiter state
# ---------------------------------------------------------------------------
_request_timestamps: list[float] = []


def _rate_limit_check() -> float:
    """
    Check rate limit and return sleep time if needed.
    Returns 0.0 if request can proceed immediately.
    """
    global _request_timestamps
    now = time.time()

    # Remove timestamps outside the window
    cutoff = now - RATE_LIMIT_WINDOW
    _request_timestamps = [ts for ts in _request_timestamps if ts > cutoff]

    if len(_request_timestamps) < RATE_LIMIT_REQUESTS:
        _request_timestamps.append(now)
        return 0.0

    # Need to wait
    oldest_in_window = min(_request_timestamps)
    sleep_time = (oldest_in_window + RATE_LIMIT_WINDOW) - now
    return max(sleep_time, 0.0)


# ---------------------------------------------------------------------------
# PubMedService
# ---------------------------------------------------------------------------
class PubMedService:
    """Service for searching and retrieving PubMed articles."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or NCBI_API_KEY
        self.base_url = NCBI_BASE_URL
        self.client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self.client is None or self.client.is_closed:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=10.0),
                headers={"User-Agent": "GuardianHealth/2.0 (support@guardian.health)"},
            )
        return self.client

    async def close(self) -> None:
        if self.client and not self.client.is_closed:
            await self.client.aclose()
            self.client = None

    def _cache_key(self, search_terms: list[str], symptoms: list[str]) -> str:
        """Generate cache key from search parameters."""
        terms = "|".join(sorted(search_terms))
        syms = "|".join(sorted(symptoms))
        return f"pubmed:{terms}:{syms}"

    async def search_pubmed(
        self,
        search_terms: list[str],
        symptoms: list[str] | None = None,
        max_results: int = 5,
    ) -> dict[str, Any]:
        """
        Search PubMed for articles matching the given terms.

        Args:
            search_terms: Primary search terms (e.g., condition names).
            symptoms: Associated symptoms for query enrichment.
            max_results: Maximum number of abstracts to retrieve.

        Returns:
            Dict with query info and list of article summaries.
        """
        symptoms = symptoms or []
        cache_key = self._cache_key(search_terms, symptoms)

        # Check cache
        if cache_key in _pubmed_cache:
            logger.debug("PubMed cache hit for key: %s", cache_key)
            return _pubmed_cache[cache_key]

        # Rate limiting
        sleep_time = _rate_limit_check()
        if sleep_time > 0:
            logger.debug("Rate limiting: sleeping %.2fs", sleep_time)
            time.sleep(sleep_time)

        # Build search query
        query_parts = search_terms[:3]  # Limit to top 3 terms
        if symptoms:
            query_parts.extend(symptoms[:2])
        query = " AND ".join(f'"{term}"[Title/Abstract]' for term in query_parts)

        params: dict[str, str] = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": str(max_results),
            "sort": "relevance",
        }
        if self.api_key:
            params["api_key"] = self.api_key

        try:
            client = await self._get_client()

            # Step 1: Search for IDs
            search_url = f"{self.base_url}/esearch.fcgi"
            resp = await client.get(search_url, params=params)
            resp.raise_for_status()
            search_data = resp.json()

            id_list = search_data.get("esearchresult", {}).get("idlist", [])
            if not id_list:
                result = {
                    "query": query,
                    "total_count": 0,
                    "articles": [],
                    "cached": False,
                }
                _pubmed_cache[cache_key] = result
                return result

            # Step 2: Fetch summaries
            summary_params = {
                "db": "pubmed",
                "id": ",".join(id_list),
                "retmode": "json",
            }
            if self.api_key:
                summary_params["api_key"] = self.api_key

            summary_url = f"{self.base_url}/esummary.fcgi"
            resp = await client.get(summary_url, params=summary_params)
            resp.raise_for_status()
            summary_data = resp.json()

            # Step 3: Fetch abstracts (XML)
            abstract_params = {
                "db": "pubmed",
                "id": ",".join(id_list),
                "retmode": "xml",
            }
            if self.api_key:
                abstract_params["api_key"] = self.api_key

            fetch_url = f"{self.base_url}/efetch.fcgi"
            resp = await client.get(fetch_url, params=abstract_params)
            resp.raise_for_status()
            xml_content = resp.text

            abstracts = self._parse_abstracts_xml(xml_content, id_list)

            # Build article list
            articles = []
            result_summary = summary_data.get("result", {})
            for uid in id_list:
                doc = result_summary.get(uid, {})
                abstract_data = abstracts.get(uid, {})

                articles.append({
                    "pmid": uid,
                    "title": doc.get("title", "No title"),
                    "abstract": abstract_data.get("abstract", "Abstract not available"),
                    "authors": [a.get("name", "") for a in doc.get("authors", [])[:3]],
                    "journal": doc.get("source", ""),
                    "pub_date": doc.get("pubdate", ""),
                    "doi": doc.get("elocationid", ""),
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                })

            result = {
                "query": query,
                "total_count": int(search_data.get("esearchresult", {}).get("count", 0)),
                "articles": articles,
                "cached": False,
            }

            # Cache result
            _pubmed_cache[cache_key] = result
            return result

        except httpx.HTTPError as exc:
            logger.error("PubMed API HTTP error: %s", exc)
            return {"query": "", "total_count": 0, "articles": [], "error": f"HTTP error: {exc}"}
        except Exception as exc:
            logger.error("PubMed search error: %s", exc)
            return {"query": "", "total_count": 0, "articles": [], "error": f"Error: {exc}"}

    @staticmethod
    def _parse_abstracts_xml(xml_content: str, id_list: list[str]) -> dict[str, dict[str, str]]:
        """Parse PubMed XML to extract abstracts by PMID."""
        abstracts: dict[str, dict[str, str]] = {}

        try:
            root = ET.fromstring(xml_content)
            ns = {"pubmed": "http://dtd.nlm.nih.gov/ncbi/pubmed/out/090101/MINI_DTD/"}

            # Try with namespace first
            articles = root.findall(".//pubmed:PubmedArticle", ns)
            if not articles:
                # Try without namespace
                articles = root.findall(".//PubmedArticle")

            for article in articles:
                pmid_elem = article.find(".//PMID")
                if pmid_elem is None:
                    continue
                pmid = pmid_elem.text or ""

                abstract_elem = article.find(".//Abstract/AbstractText")
                if abstract_elem is None:
                    # Try alternative paths
                    abstract_elem = article.find(".//AbstractText")

                abstract_text = ""
                if abstract_elem is not None:
                    abstract_text = abstract_elem.text or ""
                    # Handle multiple AbstractText elements with labels
                    if not abstract_text:
                        parts = []
                        for at in article.findall(".//AbstractText"):
                            label = at.get("Label", "")
                            text = at.text or ""
                            if label and text:
                                parts.append(f"{label}: {text}")
                            elif text:
                                parts.append(text)
                        abstract_text = " ".join(parts)

                if pmid:
                    abstracts[pmid] = {"abstract": abstract_text or "Abstract not available"}

            # Fill in missing PMIDs
            for pmid in id_list:
                if pmid not in abstracts:
                    abstracts[pmid] = {"abstract": "Abstract not available"}

        except ET.ParseError as exc:
            logger.warning("PubMed XML parse error: %s", exc)
            for pmid in id_list:
                abstracts[pmid] = {"abstract": "Abstract parsing failed"}

        return abstracts

    @classmethod
    async def search_in_background(
        cls,
        search_terms: list[str],
        symptoms: list[str] | None = None,
        max_results: int = 3,
    ) -> dict[str, Any]:
        """
        Static method for BackgroundTasks-compatible execution.
        Fire-and-forget: results can be stored separately.
        """
        service = cls()
        try:
            result = await service.search_pubmed(search_terms, symptoms, max_results)
            logger.info(
                "Background PubMed search completed: %d articles for terms %s",
                len(result.get("articles", [])),
                search_terms,
            )
            return result
        finally:
            await service.close()
