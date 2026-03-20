"""Chat router – main Q&A endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.agents.orchestrator import orchestrator
from app.models.schemas import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Handle a user question through the orchestration pipeline."""
    try:
        return await orchestrator.process(request)
    except Exception as e:
        logger.error("Chat processing failed: %s", e, exc_info=True)
        raise HTTPException(status_code=502, detail=f"LLM 服务调用失败，请检查配置: {e}")
