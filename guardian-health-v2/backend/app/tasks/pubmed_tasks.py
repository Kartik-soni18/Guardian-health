"""PubMed search Celery task with NCBI E-utilities API."""

from __future__ import annotations

import logging
import os
import time
import xml.etree.ElementTree as ET
from typing import Any

logger = logging.getLogger(__name__)

# NCBI configuration
NCBI_EMAIL = os.environ.get("NCBI_EMAIL", "guardian-health@example.com")
NCBI_API_KEY = os.environ.get("NCBI_API_KEY", "")
NCBI_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
NCBI_RATE_LIMIT_DELAY = 0.34 if NCBI_API_KEY else 1.0  # 10 req/s with key, 3 req/s without


def _ncbi_request(url: str, params: dict[str, str]) -> str:
    """Make a request to NCBI E-utilities with rate limiting."""
    import urllib.request
    import urllib.parse

    # Add API key and email if available
    params["email"] = NCBI_EMAIL
    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY

    query_string = urllib.parse.urlencode(params)
    full_url = f"{url}?{query_string}"

    # Rate limiting
    time.sleep(NCBI_RATE_LIMIT_DELAY)

    req = urllib.request.Request(
        full_url,
        headers={"User-Agent": f"GuardianHealth/2.0 ({NCBI_EMAIL})"},
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode("utf-8")
    except Exception:
        logger.exception("NCBI request failed: %s", full_url)
        raise


def _parse_pubmed_article(article_elem: ET.Element) -> dict[str, Any] | None:
    """Parse a PubMed Article XML element into a dict."""
    try:
        medline = article_elem.find("MedlineCitation")
        if medline is None:
            return None

        article = medline.find("Article")
        if article is None:
            return None

        # PMID
        pmid_elem = medline.find("PMID")
        pmid = pmid_elem.text if pmid_elem is not None else ""

        # Title
        title_elem = article.find("ArticleTitle")
        title = title_elem.text if title_elem is not None else "Untitled"

        # Abstract
        abstract_elem = article.find("Abstract")
        abstract = ""
        if abstract_elem is not None:
            abstract_parts = []
            for abs_text in abstract_elem.findall("AbstractText"):
                if abs_text.text:
                    label = abs_text.get("Label", "")
                    if label:
                        abstract_parts.append(f"{label}: {abs_text.text}")
                    else:
                        abstract_parts.append(abs_text.text)
            abstract = " ".join(abstract_parts)

        # Journal
        journal_elem = article.find("Journal")
        journal = ""
        year = ""
        if journal_elem is not None:
            title_elem_j = journal_elem.find("Title")
            if title_elem_j is not None and title_elem_j.text:
                journal = title_elem_j.text

            # Year
            journal_issue = journal_elem.find("JournalIssue")
            if journal_issue is not None:
                pub_date = journal_issue.find("PubDate")
                if pub_date is not None:
                    year_elem = pub_date.find("Year")
                    if year_elem is not None and year_elem.text:
                        year = year_elem.text
                    else:
                        medline_date = pub_date.find("MedlineDate")
                        if medline_date is not None and medline_date.text:
                            year = medline_date.text[:4]

        # Authors
        author_list = article.find("AuthorList")
        authors: list[str] = []
        if author_list is not None:
            for author in author_list.findall("Author")[:3]:  # First 3 authors
                last_name = author.find("LastName")
                initials = author.find("Initials")
                if last_name is not None and last_name.text:
                    name = last_name.text
                    if initials is not None and initials.text:
                        name += f" {initials.text}"
                    authors.append(name)

        # URL
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""

        return {
            "pmid": pmid,
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "journal": journal,
            "year": year,
            "url": url,
        }

    except Exception:
        logger.exception("Failed to parse PubMed article")
        return None


# ── Celery task ──

try:
    from celery import shared_task

    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    logger.warning("Celery not installed — PubMed task will not be available")

    # Stub decorator for when Celery is not available
    def shared_task(*args: Any, **kwargs: Any) -> Any:
        def decorator(func: Any) -> Any:
            func.delay = lambda **kw: logger.warning("Celery not available, task not executed")
            return func
        return decorator


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
)
def search_pubmed(self, search_terms: list[str], symptoms: list[str]) -> list[dict[str, Any]]:
    """Search PubMed for articles related to the given search terms and symptoms.

    Uses NCBI E-utilities API with proper rate limiting.
    Supports NCBI API key for 10 req/s throughput.

    Args:
        search_terms: List of search terms derived from clinical extraction.
        symptoms: List of patient symptoms for additional context.

    Returns:
        List of article dicts with title, abstract, url, year, journal, authors.
    """
    if not search_terms and not symptoms:
        logger.warning("search_pubmed: no search terms or symptoms provided")
        return []

    # Build search query
    all_terms = list(search_terms) + list(symptoms)
    query = " AND ".join(f'"{term}"' for term in all_terms[:5])

    logger.info("search_pubmed: query=%s", query)

    try:
        # Step 1: ESearch — get IDs
        search_params = {
            "db": "pubmed",
            "term": query,
            "retmax": "10",
            "retmode": "json",
            "sort": "relevance",
        }

        search_response = _ncbi_request(f"{NCBI_BASE_URL}/esearch.fcgi", search_params)
        search_data = __import__("json").loads(search_response)
        id_list = search_data.get("esearchresult", {}).get("idlist", [])

        if not id_list:
            logger.info("search_pubmed: no results found for query=%s", query)
            return []

        logger.info("search_pubmed: found %d article IDs", len(id_list))

        # Step 2: EFetch — get article details
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "xml",
        }

        fetch_response = _ncbi_request(f"{NCBI_BASE_URL}/efetch.fcgi", fetch_params)

        # Parse XML response
        root = ET.fromstring(fetch_response)
        articles: list[dict[str, Any]] = []

        for pubmed_article in root.findall("PubmedArticle"):
            parsed = _parse_pubmed_article(pubmed_article)
            if parsed:
                articles.append(parsed)

        logger.info("search_pubmed: parsed %d articles", len(articles))
        return articles

    except Exception as exc:
        logger.exception("search_pubmed: search failed")
        # Retry will be handled by Celery autoretry
        raise self.retry(exc=exc) if CELERY_AVAILABLE else exc
