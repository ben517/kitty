"""Vector store management backed by ChromaDB."""

from __future__ import annotations

import logging
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings

logger = logging.getLogger(__name__)

_client: Optional[chromadb.ClientAPI] = None


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        # Force local implementation by setting chroma_api_impl
        chroma_settings = ChromaSettings(
            anonymized_telemetry=False,
            chroma_api_impl="chromadb.api.segment.SegmentAPI",  # Force local segment API
        )
        _client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=chroma_settings,
        )
    return _client


def get_collection() -> chromadb.Collection:
    client = _get_client()
    return client.get_or_create_collection(
        name=settings.chroma_collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def add_documents(
    texts: list[str],
    metadatas: list[dict],
    ids: list[str],
    embeddings: list[list[float]],
) -> None:
    """Upsert document chunks with pre-computed embeddings."""
    collection = get_collection()
    collection.upsert(
        documents=texts,
        metadatas=metadatas,
        ids=ids,
        embeddings=embeddings,
    )
    logger.info("Upserted %d chunks into collection '%s'", len(ids), settings.chroma_collection_name)


def query_by_embedding(
    query_embedding: list[float],
    top_k: int = settings.rag_top_k,
    where: Optional[dict] = None,
) -> dict:
    """Query the collection by embedding vector."""
    collection = get_collection()
    params: dict = {
        "query_embeddings": [query_embedding],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        params["where"] = where
    return collection.query(**params)


def query_by_text(
    query_text: str,
    top_k: int = settings.rag_top_k,
    where: Optional[dict] = None,
) -> dict:
    """Keyword-based query using ChromaDB's built-in full-text search."""
    collection = get_collection()
    params: dict = {
        "query_texts": [query_text],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        params["where"] = where
    return collection.query(**params)
