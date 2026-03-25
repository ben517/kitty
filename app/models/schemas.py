"""Pydantic models for API request/response schemas."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------- Chat ----------

class ChatRequest(BaseModel):
    query: str = Field(..., description="用户问题")
    session_id: Optional[str] = Field(None, description="会话 ID，用于多轮对话")


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = Field(default_factory=list, description="引用的知识来源")
    device_id: Optional[str] = None
    session_id: Optional[str] = None
    intent: Optional[str] = Field(None, description="识别的意图类型")


# ---------- Intent ----------

class IntentType(str, Enum):
    DEVICE_STATUS = "device_status"          # 设备状态查询
    DEVICE_SIGNAL = "device_signal"          # 设备信号识别
    TECH_PARAM = "tech_param"                # 技术参数查询
    OPERATION_GUIDE = "operation_guide"      # 操作步骤指导
    FAULT_CODE = "fault_code"               # 故障代码解释
    DEVICE_LIST = "device_list"             # 列出所有设备
    GENERAL_QA = "general_qa"               # 一般知识问答


class IntentResult(BaseModel):
    intent: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    entities: dict = Field(default_factory=dict, description="提取的实体：device_id, device_type 等")


# ---------- Knowledge ----------

class DocumentUploadResponse(BaseModel):
    filename: str
    chunk_count: int
    status: str = "success"


# ---------- Device ----------

class DeviceInfo(BaseModel):
    device_id: str
    name: Optional[str] = None
    label: Optional[str] = None
    device_type: Optional[str] = None
    room: Optional[str] = None


class DeviceStatus(BaseModel):
    device_id: str
    components: dict = Field(default_factory=dict)


class DeviceHealth(BaseModel):
    device_id: str
    state: Optional[str] = None
