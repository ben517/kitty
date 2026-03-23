"""Orchestrator Agent – intent recognition, routing and result fusion."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Optional

from app.agents.device_info import device_info_agent
from app.models.schemas import ChatRequest, ChatResponse, IntentResult, IntentType
from app.rag.generator import generate_answer
from app.rag.llm import chat_completion
from app.rag.reranker import rerank
from app.rag.retriever import multi_recall

logger = logging.getLogger(__name__)

# In-memory session store (replace with Redis / DB for production)
_sessions: dict[str, list[dict]] = {}

_INTENT_PROMPT = """\
你是一个意图识别助手。根据用户的问题，判断其意图类型并提取关键实体。

意图类型：
- device_status: 设备状态查询（如"空调现在开着吗"、"洗衣机运行到哪一步了"、"灯亮着吗"）
- device_signal: 设备信号/健康状态识别（如"设备是否在线"、"信号强度如何"）
- tech_param: 技术参数/功能/规格/厂商查询（如"这款冰箱的容量是多少"、"额定功率是多少"、"有哪些功能"、"支持什么模式"、"参数规格"、"是什么牌子"、"哪个厂家生产的"、"制造商是谁"）
- operation_guide: 操作步骤指导（如"怎么设置定时"、"如何连接WiFi"、"怎么使用"）
- fault_code: 故障代码解释（如"E3是什么故障"、"显示F5怎么办"）
- device_list: 列出设备清单（如"我有哪些设备"、"当前有什么设备"、"显示所有设备"）
- general_qa: 一般知识问答（不属于以上类别的设备相关问题）

注意：询问"有什么功能"、"支持哪些模式"、"功能介绍"、"品牌/制造商/厂家"属于 tech_param 类型。

请返回 JSON，包含：
- "intent": 意图类型字符串
- "confidence": 0-1 之间的置信度
- "entities": 提取的实体字典，可能包含 device_id, device_type, fault_code 等

用户问题：{query}
"""


class OrchestratorAgent:
    """Main orchestration agent that routes queries to sub-agents."""

    async def recognize_intent(self, query: str) -> IntentResult:
        """Use LLM to classify the user's intent."""
        prompt = _INTENT_PROMPT.format(query=query)
        try:
            raw = chat_completion([{"role": "user", "content": prompt}], temperature=0.0)
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
            data = json.loads(raw)
            return IntentResult(
                intent=IntentType(data["intent"]),
                confidence=float(data.get("confidence", 0.8)),
                entities=data.get("entities", {}),
            )
        except Exception:
            logger.warning("Intent recognition failed, defaulting to general_qa", exc_info=True)
            return IntentResult(intent=IntentType.GENERAL_QA, confidence=0.5)

    async def process(self, request: ChatRequest) -> ChatResponse:
        """Full pipeline: intent -> route -> answer."""

        session_id = request.session_id or str(uuid.uuid4())

        # Store conversation history
        history = _sessions.setdefault(session_id, [])
        history.append({"role": "user", "content": request.query})

        # --- Intent recognition ---
        intent_result = await self.recognize_intent(request.query)
        logger.info(
            "Intent: %s (confidence=%.2f) entities=%s",
            intent_result.intent.value,
            intent_result.confidence,
            intent_result.entities,
        )

        # Determine device_id from request or extracted entities
        device_id = request.device_id or intent_result.entities.get("device_id")
        device_type = request.device_type or intent_result.entities.get("device_type")

        # --- Route to appropriate agent ---
        if intent_result.intent in (
            IntentType.DEVICE_STATUS,
            IntentType.DEVICE_SIGNAL,
            IntentType.TECH_PARAM,
            IntentType.OPERATION_GUIDE,
            IntentType.FAULT_CODE,
            IntentType.DEVICE_LIST,
        ):
            result = await device_info_agent.handle(
                query=request.query,
                intent=intent_result.intent,
                device_id=device_id,
                device_type=device_type,
            )
        else:
            # general_qa – RAG only, no API call
            result = await self._handle_general_qa(request.query, device_type)

        answer = result["answer"]
        sources = result.get("sources", [])
        # Use device_id from result if available (resolved by device_info_agent)
        device_id = result.get("device_id") or device_id

        # Save assistant response in session
        history.append({"role": "assistant", "content": answer})

        return ChatResponse(
            answer=answer,
            sources=sources,
            device_id=device_id,
            session_id=session_id,
        )

    async def _handle_general_qa(self, query: str, device_type: Optional[str] = None) -> dict:
        where: Optional[dict] = None
        if device_type:
            where = {"device_type": device_type}

        chunks = multi_recall(query, where=where)
        chunks = rerank(query, chunks)
        answer = generate_answer(query, chunks)
        sources = list({c.metadata.get("filename", "") for c in chunks if c.metadata.get("filename")})
        return {"answer": answer, "sources": sources}


orchestrator = OrchestratorAgent()
