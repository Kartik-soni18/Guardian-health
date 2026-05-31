import logging
import os
import xml.etree.ElementTree as ET

import httpx

logger = logging.getLogger(__name__)

_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
_EFETCH_URL  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
_PUBMED_BASE = "https://pubmed.ncbi.nlm.nih.gov"
_NCBI_TOOL   = "GuardianHealth"
_NCBI_EMAIL  = os.getenv("NCBI_EMAIL", "guardian-health@example.com")
_LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234")
_MODEL_ID      = os.getenv("LM_STUDIO_MODEL", "QuantFactory/Bio-Medical-Llama-3-8B-GGUF")


def search_pubmed(clinical_entities: dict) -> dict:
    search_terms = clinical_entities.get("search_terms") or []
    symptoms     = clinical_entities.get("symptoms") or []
    severity     = clinical_entities.get("severity")

    query_parts = search_terms if search_terms else symptoms[:3]
    if not query_parts:
        return _empty_result("No search terms available")

    symptom_query = " OR ".join(f'"{term}"' for term in query_parts[:3])
    filters = ["(Review[pt] OR Clinical Trial[pt] OR Systematic Review[pt] OR Meta-Analysis[pt] OR Practice Guideline[pt])"]
    if severity in ("severe", "moderate"):
        filters.append(f'("{severity}"[tiab])')

    pubmed_query = f"({symptom_query}) AND {' AND '.join(filters)}"
    logger.info("[PubMed] Query: %s", pubmed_query)

    pmids = _esearch(pubmed_query)

    if not pmids:
        simple = f"({symptom_query})"
        pmids = _esearch(simple)
        pubmed_query = simple

    if not pmids and symptoms:
        fallback = f'"{symptoms[0]}"'
        pmids = _esearch(fallback)
        pubmed_query = fallback

    if not pmids:
        return _empty_result(f"No results for: {pubmed_query}")

    articles = _efetch(pmids)
    if not articles:
        return _empty_result("Could not retrieve abstracts from NCBI")

    articles = _rank_articles(articles, symptoms, severity)
    summary = _summarise(articles, clinical_entities)

    return {
        "articles":    articles,
        "summary":     summary,
        "source":      "PubMed / NCBI",
        "query_used":  pubmed_query,
        "total_found": len(articles),
    }


def _esearch(query: str, max_results: int = 5) -> list[str]:
    params = {
        "db": "pubmed", "term": query, "retmax": max_results,
        "retmode": "json", "sort": "relevance",
        "datetype": "pdat", "reldate": 3650,
        "tool": _NCBI_TOOL, "email": _NCBI_EMAIL,
    }
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(_ESEARCH_URL, params=params)
            resp.raise_for_status()
        pmids = resp.json().get("esearchresult", {}).get("idlist", [])
        logger.info("[PubMed] esearch returned %d PMIDs", len(pmids))
        return pmids
    except Exception as exc:
        logger.error("[PubMed] esearch error: %s", exc)
        return []


def _efetch(pmids: list[str]) -> list[dict]:
    if not pmids:
        return []
    params = {
        "db": "pubmed", "id": ",".join(pmids),
        "retmode": "xml", "rettype": "abstract",
        "tool": _NCBI_TOOL, "email": _NCBI_EMAIL,
    }
    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.get(_EFETCH_URL, params=params)
            resp.raise_for_status()
        return _parse_xml(resp.text)
    except Exception as exc:
        logger.error("[PubMed] efetch error: %s", exc)
        return []


def _parse_xml(xml_text: str) -> list[dict]:
    articles = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        logger.error("[PubMed] XML parse error: %s", exc)
        return []

    for article_el in root.findall(".//PubmedArticle"):
        try:
            pmid_el   = article_el.find(".//PMID")
            title_el  = article_el.find(".//ArticleTitle")
            year_el   = article_el.find(".//PubDate/Year")
            jrnl_el   = article_el.find(".//Journal/Title")
            abs_texts = article_el.findall(".//AbstractText")

            pmid     = pmid_el.text if pmid_el is not None else "Unknown"
            title    = "".join(title_el.itertext()) if title_el is not None else "Untitled"
            year     = year_el.text if year_el is not None else "N/A"
            journal  = jrnl_el.text if jrnl_el is not None else "Unknown Journal"
            abstract = " ".join("".join(t.itertext()) for t in abs_texts).strip() if abs_texts else "Abstract not available."

            articles.append({
                "pmid": pmid, "title": title[:250], "abstract": abstract[:1800],
                "url": f"{_PUBMED_BASE}/{pmid}/", "year": year, "journal": journal,
            })
        except Exception as exc:
            logger.warning("[PubMed] Skipping malformed article: %s", exc)

    return articles[:5]


def _rank_articles(articles: list[dict], symptoms: list[str], severity: str = None) -> list[dict]:
    if not articles or not symptoms:
        return articles[:3]

    symptom_terms = {w for s in symptoms for w in s.lower().split() if len(w) > 3}
    scored = []
    for article in articles:
        score = 0
        title_lower    = article.get("title", "").lower()
        abstract_lower = article.get("abstract", "").lower()

        for term in symptom_terms:
            if term in title_lower:    score += 3
            if term in abstract_lower: score += 1

        for kw in ["review", "guideline", "meta-analysis", "systematic", "clinical trial"]:
            if kw in title_lower or kw in abstract_lower[:200]:
                score += 2

        try:
            year = int(article.get("year", "0"))
            if year >= 2022: score += 2
            elif year >= 2018: score += 1
        except ValueError:
            pass

        if article.get("abstract", "").startswith("Abstract not available"):
            score -= 5

        scored.append((score, article))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [a for _, a in scored[:3]]


def _summarise(articles: list[dict], clinical_entities: dict) -> str:
    if not articles:
        return "No PubMed abstracts were available for summarisation."

    symptoms_str = ", ".join(clinical_entities.get("symptoms") or ["the described symptoms"])
    abstracts_block = "\n\n".join(
        f"[{i+1}] {a['title']} ({a['year']}, {a['journal']}):\n{a['abstract']}"
        for i, a in enumerate(articles)
    )

    prompt = (
        f"You are a medical research summariser. Based on the PubMed abstracts below about '{symptoms_str}', "
        f"write a concise 3-4 sentence patient-friendly overview.\n\n"
        f"Rules:\n- Begin with: 'According to recent PubMed research...'\n"
        f"- Do NOT state a diagnosis.\n- Do NOT recommend specific medications.\n\n"
        f"ABSTRACTS:\n{abstracts_block}"
    )

    try:
        with httpx.Client(timeout=25.0) as client:
            resp = client.post(
                f"{_LM_STUDIO_URL}/v1/chat/completions",
                json={"model": _MODEL_ID, "messages": [{"role": "user", "content": prompt}], "temperature": 0.3, "max_tokens": 350},
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
        summary = resp.json()["choices"][0]["message"]["content"].strip()
        logger.info("[PubMed] Summary generated (%d chars)", len(summary))
        return summary
    except Exception as exc:
        logger.warning("[PubMed] Summarisation failed: %s — fallback", exc)
        return "According to PubMed research: " + " ".join(a["abstract"].split(".")[0] + "." for a in articles[:3])


def _empty_result(reason: str) -> dict:
    logger.warning("[PubMed] Empty result: %s", reason)
    return {
        "articles": [], "summary": "No relevant PubMed research could be retrieved.",
        "source": "PubMed / NCBI", "query_used": "", "total_found": 0, "error": reason,
    }
