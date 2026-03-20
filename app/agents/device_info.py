"""Device Information Agent – handles device-related queries via API + RAG."""

from __future__ import annotations

import json
import logging
from typing import Optional

from app.api.smartthings import smartthings
from app.models.schemas import IntentType
from app.rag.generator import generate_answer
from app.rag.reranker import rerank
from app.rag.retriever import multi_recall

logger = logging.getLogger(__name__)


class DeviceInfoAgent:
    """Agent responsible for answering device-related questions.

    Capabilities:
    - 设备状态查询
    - 设备信号识别
    - 技术参数查询
    - 操作步骤指导
    - 故障代码解释
    """

    async def handle(
        self,
        query: str,
        intent: IntentType,
        device_id: Optional[str] = None,
        device_type: Optional[str] = None,
    ) -> dict:
        """Process a device-related query and return answer + sources."""

        # --- 设备列表查询，直接调用 API 返回 ---
        if intent == IntentType.DEVICE_LIST:
            return await self._handle_device_list(query)

        # Build metadata filter for RAG
        where: Optional[dict] = None
        if device_type:
            where = {"device_type": device_type}

        # --- Step 1: Retrieve from knowledge base ---
        chunks = multi_recall(query, where=where)
        chunks = rerank(query, chunks)

        # --- Step 2: Fetch live device info if device_id is provided ---
        extra_context = ""
        if device_id:
            extra_context = await self._fetch_device_context(intent, device_id)

        # --- Step 3: Generate answer ---
        answer = generate_answer(query, chunks, extra_context=extra_context)

        sources = list({c.metadata.get("filename", "") for c in chunks if c.metadata.get("filename")})

        return {
            "answer": answer,
            "sources": sources,
            "device_id": device_id,
        }

    async def _handle_device_list(self, query: str) -> dict:
        """Fetch all devices and summarize with LLM."""
        try:
            data = await smartthings.get_devices()
            items = data.get("items", [])
            device_lines = []
            for d in items:
                label = d.get("label") or d.get("name", "未知设备")
                category = ""
                components = d.get("components", [])
                if components:
                    cats = components[0].get("categories", [])
                    if cats:
                        category = cats[0].get("name", "")
                device_lines.append(f"- {label}（{category}，ID: {d['deviceId']}）")
            device_summary = "\n".join(device_lines) if device_lines else "未找到任何设备"
            extra_context = f"当前账号下共有 {len(items)} 台设备：\n{device_summary}"
        except Exception:
            logger.warning("Failed to fetch device list", exc_info=True)
            extra_context = "无法获取设备列表，请检查 SmartThings 配置。"

        answer = generate_answer(query, [], extra_context=extra_context)
        return {"answer": answer, "sources": []}

    async def _fetch_device_context(self, intent: IntentType, device_id: str) -> str:
        """Fetch real-time device information from SmartThings API."""
        try:
            if intent == IntentType.DEVICE_STATUS:
                data = await smartthings.get_device_status(device_id)
                return f"设备当前状态：{json.dumps(data, ensure_ascii=False)}"

            if intent == IntentType.DEVICE_SIGNAL:
                data = await smartthings.get_device_health(device_id)
                return f"设备健康状态：{json.dumps(data, ensure_ascii=False)}"

            if intent == IntentType.TECH_PARAM:
                data = await smartthings.get_device_capabilities(device_id)
                return f"设备能力信息：{json.dumps(data, ensure_ascii=False)}"

            # For other intents, fetch basic device info
            data = await smartthings.get_device(device_id)
            return f"设备信息：{json.dumps(data, ensure_ascii=False)}"

        except Exception:
            logger.warning("Failed to fetch device info for %s", device_id, exc_info=True)
            return ""


device_info_agent = DeviceInfoAgent()
