"""Re-ranker – LLM-based relevance scoring for retrieved chunks."""

from __future__ import annotations

import json
import logging

from app.config import settings
from app.rag.llm import chat_completion
from app.rag.retriever import RetrievedChunk

logger = logging.getLogger(__name__)

_RERANK_PROMPT = """\
你是一个相关性评分助手。给定一个用户问题和一组候选文本段落，请为每个段落评估其与问题的相关性。
返回 JSON 数组，每个元素包含 "index"（段落序号，从0开始）和 "score"（0-10的相关性评分）。

用户问题：{query}

候选段落：
{passages}

请仅返回 JSON 数组，不要添加其他内容。
"""


def rerank(
    query: str,
    chunks: list[RetrievedChunk],
    top_n: int = settings.rag_rerank_top_n,
) -> list[RetrievedChunk]:
    """Use LLM to re-rank chunks by relevance, return top *top_n*."""
    if len(chunks) <= top_n:
        return chunks

    passages = "\n".join(
        f"[{i}] {c.text[:300]}" for i, c in enumerate(chunks)
    )
    prompt = _RERANK_PROMPT.format(query=query, passages=passages)

    try:
        raw = chat_completion([{"role": "user", "content": prompt}], temperature=0.0)
        # Extract JSON array from response
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        scores = json.loads(raw)
        score_map = {item["index"]: item["score"] for item in scores}

        ranked = sorted(chunks, key=lambda c: score_map.get(chunks.index(c), 0), reverse=True)
        return ranked[:top_n]
    except Exception:
        logger.warning("Rerank LLM call failed, falling back to original order", exc_info=True)
        return chunks[:top_n]
