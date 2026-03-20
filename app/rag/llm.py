"""LLM helper – thin wrapper around litellm for embeddings and completions."""

from __future__ import annotations

import litellm

from app.config import settings


def get_embedding(text: str) -> list[float]:
    """Return an embedding vector for *text* using the configured model."""
    resp = litellm.embedding(
        model=settings.embedding_model,
        input=[text],
        api_key=settings.embedding_api_key or None,
        api_base=settings.embedding_base_url or None,
        encoding_format="float",
    )
    return resp.data[0]["embedding"]


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Batch embedding for multiple texts."""
    resp = litellm.embedding(
        model=settings.embedding_model,
        input=texts,
        api_key=settings.embedding_api_key or None,
        api_base=settings.embedding_base_url or None,
        encoding_format="float",
    )
    return [d["embedding"] for d in resp.data]


def chat_completion(messages: list[dict], temperature: float = 0.3) -> str:
    """Single-turn chat completion via litellm."""
    resp = litellm.completion(
        model=settings.llm_model,
        messages=messages,
        temperature=temperature,
        api_key=settings.llm_api_key or None,
        api_base=settings.llm_base_url or None,
    )
    return resp.choices[0].message.content
