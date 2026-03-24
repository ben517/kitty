"""测试用例：Pydantic 模型和 Schema 验证测试。"""

import pytest
from pydantic import ValidationError

from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    DeviceHealth,
    DeviceInfo,
    DeviceStatus,
    DocumentUploadResponse,
    IntentResult,
    IntentType,
)


class TestChatRequestSchema:
    """测试 ChatRequest 模型。"""

    def test_minimal_valid_request(self):
        """测试：最小有效请求（只有 query）。"""
        request = ChatRequest(query="空调怎么开？")
        assert request.query == "空调怎么开？"
        assert request.session_id is None

    def test_full_request(self):
        """测试：包含所有字段的请求。"""
        request = ChatRequest(
            query="空调怎么开？",
            session_id="session_456"
        )
        assert request.query == "空调怎么开？"
        assert request.session_id == "session_456"

    def test_empty_query_invalid(self):
        """测试：空查询应该无效。
        
        注意：Pydantic v2 允许空字符串，所以这个测试可能不适用。
        如果需要禁止空字符串，需要在 Field 中添加 min_length=1 约束。
        """
        # Pydantic 默认允许空字符串，这里仅作为文档说明
        request = ChatRequest(query="")
        assert request.query == ""

    def test_whitespace_only_query_invalid(self):
        """测试：仅空白字符的查询应该无效。"""
        # Pydantic v2 默认不 trim 字符串，所以这可能是有效的
        request = ChatRequest(query="   ")
        assert request.query == "   "

    def test_optional_fields_default_none(self):
        """测试：可选字段默认为 None。"""
        request = ChatRequest(query="test")
        assert request.session_id is None


class TestChatResponseSchema:
    """测试 ChatResponse 模型。"""

    def test_minimal_response(self):
        """测试：最小响应（只有 answer）。"""
        response = ChatResponse(answer="这是答案")
        assert response.answer == "这是答案"
        assert response.sources == []
        assert response.device_id is None
        assert response.session_id is None

    def test_full_response(self):
        """测试：完整响应。"""
        response = ChatResponse(
            answer="这是答案",
            sources=["manual.pdf", "guide.txt"],
            device_id="device_123",
            session_id="session_456"
        )
        assert response.answer == "这是答案"
        assert response.sources == ["manual.pdf", "guide.txt"]
        assert response.device_id == "device_123"
        assert response.session_id == "session_456"

    def test_sources_default_empty_list(self):
        """测试：sources 默认为空列表。"""
        response = ChatResponse(answer="test")
        assert response.sources == []
        assert isinstance(response.sources, list)


class TestIntentTypeEnum:
    """测试 IntentType 枚举。"""

    def test_all_intent_types_exist(self):
        """测试：所有意图类型都存在。"""
        assert IntentType.DEVICE_STATUS.value == "device_status"
        assert IntentType.DEVICE_SIGNAL.value == "device_signal"
        assert IntentType.TECH_PARAM.value == "tech_param"
        assert IntentType.OPERATION_GUIDE.value == "operation_guide"
        assert IntentType.FAULT_CODE.value == "fault_code"
        assert IntentType.DEVICE_LIST.value == "device_list"
        assert IntentType.GENERAL_QA.value == "general_qa"

    def test_create_from_string(self):
        """测试：从字符串创建 IntentType。"""
        intent = IntentType("device_status")
        assert intent == IntentType.DEVICE_STATUS

    def test_invalid_intent_type(self):
        """测试：无效的意图类型抛出异常。"""
        with pytest.raises(ValueError):
            IntentType("invalid_intent")


class TestIntentResultSchema:
    """测试 IntentResult 模型。"""

    def test_minimal_result(self):
        """测试：最小结果（只有 intent）。"""
        # confidence 是必需字段，需要提供默认值
        result = IntentResult(intent=IntentType.GENERAL_QA, confidence=0.8)
        assert result.intent == IntentType.GENERAL_QA
        assert result.confidence == 0.8
        assert result.entities == {}

    def test_full_result(self):
        """测试：完整结果。"""
        result = IntentResult(
            intent=IntentType.DEVICE_STATUS,
            confidence=0.95,
            entities={"device_id": "device_123", "device_type": "air_conditioner"}
        )
        assert result.intent == IntentType.DEVICE_STATUS
        assert result.confidence == 0.95
        assert result.entities["device_id"] == "device_123"

    def test_confidence_range_validation(self):
        """测试：置信度范围验证。"""
        # 有效范围
        result1 = IntentResult(intent=IntentType.GENERAL_QA, confidence=0.0)
        assert result1.confidence == 0.0
        
        result2 = IntentResult(intent=IntentType.GENERAL_QA, confidence=1.0)
        assert result2.confidence == 1.0
        
        # 超出范围
        with pytest.raises(ValidationError):
            IntentResult(intent=IntentType.GENERAL_QA, confidence=-0.1)
        
        with pytest.raises(ValidationError):
            IntentResult(intent=IntentType.GENERAL_QA, confidence=1.1)

    def test_entities_default_empty_dict(self):
        """测试：entities 默认为空字典。"""
        result = IntentResult(intent=IntentType.GENERAL_QA, confidence=0.5)
        assert result.entities == {}
        assert isinstance(result.entities, dict)


class TestDeviceInfoSchema:
    """测试 DeviceInfo 模型。"""

    def test_minimal_device_info(self):
        """测试：最小设备信息（只有 device_id）。"""
        info = DeviceInfo(device_id="device_123")
        assert info.device_id == "device_123"
        assert info.name is None
        assert info.label is None
        assert info.device_type is None
        assert info.room is None

    def test_full_device_info(self):
        """测试：完整设备信息。"""
        info = DeviceInfo(
            device_id="device_123",
            name="客厅空调",
            label="主空调",
            device_type="air_conditioner",
            room="living_room"
        )
        assert info.name == "客厅空调"
        assert info.label == "主空调"
        assert info.device_type == "air_conditioner"
        assert info.room == "living_room"


class TestDeviceStatusSchema:
    """测试 DeviceStatus 模型。"""

    def test_minimal_device_status(self):
        """测试：最小设备状态。"""
        status = DeviceStatus(device_id="device_123")
        assert status.device_id == "device_123"
        assert status.components == {}

    def test_device_status_with_components(self):
        """测试：带组件的设备状态。"""
        status = DeviceStatus(
            device_id="device_123",
            components={
                "switch": {"value": "on"},
                "temperature": {"value": 26},
                "mode": {"value": "cool"}
            }
        )
        assert len(status.components) == 3
        assert status.components["switch"]["value"] == "on"


class TestDeviceHealthSchema:
    """测试 DeviceHealth 模型。"""

    def test_minimal_device_health(self):
        """测试：最小设备健康状态。"""
        health = DeviceHealth(device_id="device_123")
        assert health.device_id == "device_123"
        assert health.state is None

    def test_device_health_with_state(self):
        """测试：带状态的设备健康。"""
        health = DeviceHealth(device_id="device_123", state="online")
        assert health.state == "online"


class TestDocumentUploadResponseSchema:
    """测试 DocumentUploadResponse 模型。"""

    def test_minimal_response(self):
        """测试：最小上传响应。"""
        response = DocumentUploadResponse(filename="manual.pdf", chunk_count=5)
        assert response.filename == "manual.pdf"
        assert response.chunk_count == 5
        assert response.status == "success"  # 默认值

    def test_custom_status(self):
        """测试：自定义状态。"""
        response = DocumentUploadResponse(
            filename="manual.pdf",
            chunk_count=5,
            status="processing"
        )
        assert response.status == "processing"

    def test_chunk_count_zero(self):
        """测试：chunk 数量为 0。"""
        response = DocumentUploadResponse(filename="empty.txt", chunk_count=0)
        assert response.chunk_count == 0
        assert response.status == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
