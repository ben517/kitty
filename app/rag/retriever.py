"""Retriever – multi-way recall (keyword + semantic) from the vector store."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from app.config import settings
from app.knowledge.vectorstore import query_by_embedding, query_by_text
from app.rag.llm import get_embedding

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    text: str
    score: float
    metadata: dict = field(default_factory=dict)


def _normalise_results(raw: dict) -> list[RetrievedChunk]:
    """Convert ChromaDB query results into a flat list of RetrievedChunk."""
    chunks: list[RetrievedChunk] = []
    if not raw.get("documents"):
        return chunks
    docs = raw["documents"][0]
    dists = raw["distances"][0] if raw.get("distances") else [0.0] * len(docs)
    metas = raw["metadatas"][0] if raw.get("metadatas") else [{}] * len(docs)
    for doc, dist, meta in zip(docs, dists, metas):
        # ChromaDB cosine distance ∈ [0, 2]; convert to similarity
        chunks.append(RetrievedChunk(text=doc, score=1 - dist, metadata=meta))
    return chunks


def semantic_search(
    query: str,
    top_k: int = settings.rag_top_k,
    where: Optional[dict] = None,
) -> list[RetrievedChunk]:
    """Semantic (embedding-based) retrieval."""
    try:
        embedding = get_embedding(query)
        raw = query_by_embedding(embedding, top_k=top_k, where=where)
        return _normalise_results(raw)
    except Exception as e:
        logger.warning("Semantic search failed, returning empty results: %s", e)
        return []


def keyword_search(
    query: str,
    top_k: int = settings.rag_top_k,
    where: Optional[dict] = None,
) -> list[RetrievedChunk]:
    """Keyword / full-text retrieval."""
    try:
        raw = query_by_text(query, top_k=top_k, where=where)
        return _normalise_results(raw)
    except Exception as e:
        logger.warning("Keyword search failed, returning empty results: %s", e)
        return []


def multi_recall(
    query: str,
    top_k: int = settings.rag_top_k,
    where: Optional[dict] = None,
) -> list[RetrievedChunk]:
    """Multi-way recall: merge semantic and keyword results, deduplicate."""
    sem = semantic_search(query, top_k=top_k, where=where)
    kw = keyword_search(query, top_k=top_k, where=where)

    seen: set[str] = set()
    merged: list[RetrievedChunk] = []
    for chunk in sem + kw:
        key = chunk.text[:200]
        if key not in seen:
            seen.add(key)
            merged.append(chunk)

    merged.sort(key=lambda c: c.score, reverse=True)
    return merged[:top_k]
