import hashlib
import json
import logging
import os

logger = logging.getLogger(__name__)

_CHROMA_HOST     = os.getenv("CHROMA_HOST", "localhost")
_CHROMA_PORT     = int(os.getenv("CHROMA_PORT", "8000"))
_COLLECTION_NAME = "pubmed_abstracts"


def _client():
    try:
        import chromadb
        c = chromadb.HttpClient(host=_CHROMA_HOST, port=_CHROMA_PORT)
        c.heartbeat()
        return c
    except ImportError:
        logger.debug("[Cache] chromadb not installed — caching disabled")
        return None
    except Exception as exc:
        logger.debug("[Cache] ChromaDB unreachable: %s", exc)
        return None


def _collection(client):
    return client.get_or_create_collection(name=_COLLECTION_NAME, metadata={"hnsw:space": "cosine"})


def _cache_key(clinical_entities: dict, user_id: str | None = None, turn_count: int = 0) -> str:
    symptoms     = sorted(clinical_entities.get("symptoms", []))
    search_terms = sorted(clinical_entities.get("search_terms", []))
    payload      = json.dumps({
        "symptoms": symptoms,
        "search_terms": search_terms,
        "user_id": user_id or "anonymous",
        "turn_count": turn_count,
    }, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def get_cached_research(clinical_entities: dict) -> dict | None:
    c = _client()
    if not c:
        return None
    try:
        col = _collection(c)
        key = _cache_key(clinical_entities)
        result = col.get(ids=[key], include=["metadatas"])
        if result and result["ids"] and result["ids"][0]:
            logger.info("[Cache] HIT key=%s…", key[:16])
            return json.loads(result["metadatas"][0].get("result_json", "{}"))
        logger.info("[Cache] MISS key=%s…", key[:16])
        return None
    except Exception as exc:
        logger.warning("[Cache] get error: %s", exc)
        return None


def cache_research(clinical_entities: dict, research_result: dict) -> bool:
    c = _client()
    if not c:
        return False
    try:
        col = _collection(c)
        key = _cache_key(clinical_entities)
        doc_text = " ".join(
            clinical_entities.get("symptoms", []) + clinical_entities.get("search_terms", [])
        ) or "medical query"
        col.upsert(
            ids=[key],
            documents=[doc_text],
            metadatas=[{
                "result_json": json.dumps(research_result),
                "symptoms": json.dumps(clinical_entities.get("symptoms", [])),
                "source": "pubmed",
            }],
        )
        logger.info("[Cache] STORED key=%s…", key[:16])
        return True
    except Exception as exc:
        logger.warning("[Cache] store error: %s", exc)
        return False
