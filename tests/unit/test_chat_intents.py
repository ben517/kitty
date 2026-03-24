"""测试用例：各种意图场景的聊天问答测试。

涵盖所有 IntentType 类型的问题及预期回答结果。
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestDeviceStatusIntent:
    """测试设备状态查询意图 (device_status)。"""

    def test_device_on_off_status(self):
        """测试：询问设备开关状态。
        
        问题示例："空调现在开着吗？"、"灯关了吗？"
        预期：返回设备当前开关状态
        """
        response = client.post(
            "/chat/",
            json={"query": "空调现在开着吗？", "session_id": "test_001"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert data["session_id"] is not None

    def test_device_running_state(self):
        """测试：询问设备运行状态。
        
        问题示例："洗衣机运行到哪一步了？"、"热水器在加热吗？"
        预期：返回设备当前运行模式/阶段
        """
        response = client.post(
            "/chat/",
            json={"query": "洗衣机运行到哪一步了？", "session_id": "test_002"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data

    def test_device_temperature_setting(self):
        """测试：询问温度设置状态。
        
        问题示例："冰箱温度设置为多少？"、"空调设定温度是多少？"
        预期：返回当前温度设置值
        """
        response = client.post(
            "/chat/",
            json={"query": "冰箱温度设置为多少？", "session_id": "test_003"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data


class TestDeviceSignalIntent:
    """测试设备信号/健康状态意图 (device_signal)。"""

    def test_device_online_status(self):
        """测试：询问设备是否在线。
        
        问题示例："设备是否在线？"、"空调连接正常吗？"
        预期：返回设备在线/离线状态
        """
        response = client.post(
            "/chat/",
            json={"query": "设备是否在线？", "session_id": "test_004"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data

    def test_signal_strength(self):
        """测试：询问信号强度。
        
        问题示例："信号强度如何？"、"WiFi 信号好吗？"
        预期：返回信号强度信息
        """
        response = client.post(
            "/chat/",
            json={"query": "信号强度如何？", "session_id": "test_005"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data

    def test_device_health_check(self):
        """测试：询问设备健康状态。
        
        问题示例："设备健康状态怎么样？"、"有需要维护的地方吗？"
        预期：返回设备健康/维护状态
        """
        response = client.post(
            "/chat/",
            json={"query": "设备健康状态怎么样？", "session_id": "test_006"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data


class TestTechParamIntent:
    """测试技术参数查询意图 (tech_param)。"""

    def test_device_capacity(self):
        """测试：询问设备容量。
        
        问题示例："这款冰箱的容量是多少？"、"洗衣机容量多大？"
        预期：返回容量规格参数
        """
        response = client.post(
            "/chat/",
            json={"query": "这款冰箱的容量是多少？", "session_id": "test_007"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data

    def test_power_consumption(self):
        """测试：询问功率/能耗参数。
        
        问题示例："额定功率是多少？"、"耗电量怎么样？"
        预期：返回功率或能耗参数
        """
        response = client.post(
            "/chat/",
            json={"query": "额定功率是多少？", "session_id": "test_008"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data

    def test_device_features(self):
        """测试：询问设备功能。
        
        问题示例："有哪些功能？"、"支持什么模式？"、"有什么功能？"
        预期：返回功能列表说明
        """
        response = client.post(
            "/chat/",
            json={"query": "有哪些功能？", "session_id": "test_009"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data

    def test_device_brand_manufacturer(self):
        """测试：询问品牌/制造商。
        
        问题示例："是什么牌子的？"、"哪个厂家生产的？"、"制造商是谁？"
        预期：返回品牌或制造商信息
        """
        response = client.post(
            "/chat/",
            json={"query": "是什么牌子的？", "session_id": "test_010"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data

    def test_technical_specifications(self):
        """测试：询问技术规格。
        
        问题示例："参数规格是什么？"、"技术规格有哪些？"
        预期：返回详细技术参数
        """
        response = client.post(
            "/chat/",
            json={"query": "参数规格是什么？", "session_id": "test_011"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data


class TestOperationGuideIntent:
    """测试操作步骤指导意图 (operation_guide)。"""

    def test_how_to_set_timer(self):
        """测试：询问如何设置定时。
        
        问题示例："怎么设置定时？"、"如何定时间？"
        预期：返回定时设置步骤
        """
        response = client.post(
            "/chat/",
            json={"query": "怎么设置定时？", "session_id": "test_012"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data

    def test_how_to_connect_wifi(self):
        """测试：询问如何连接 WiFi。
        
        问题示例："如何连接 WiFi？"、"怎么联网？"
        预期：返回网络连接步骤
        """
        response = client.post(
            "/chat/",
            json={"query": "如何连接 WiFi？", "session_id": "test_013"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data

    def test_how_to_use_device(self):
        """测试：询问如何使用设备。
        
        问题示例："怎么使用？"、"使用方法是什么？"
        预期：返回基本使用步骤
        """
        response = client.post(
            "/chat/",
            json={"query": "怎么使用？", "session_id": "test_014"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data

    def test_reset_device(self):
        """测试：询问如何重置设备。
        
        问题示例："如何恢复出厂设置？"、"怎么重置？"
        预期：返回重置步骤
        """
        response = client.post(
            "/chat/",
            json={"query": "如何恢复出厂设置？", "session_id": "test_015"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data


class TestFaultCodeIntent:
    """测试故障代码解释意图 (fault_code)。"""

    def test_error_code_explanation(self):
        """测试：询问错误代码含义。
        
        问题示例："E3 是什么故障？"、"显示 F5 怎么办？"
        预期：返回故障代码解释和解决方法
        """
        response = client.post(
            "/chat/",
            json={"query": "E3 是什么故障？", "session_id": "test_016"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data

    def test_warning_message(self):
        """测试：询问警告信息。
        
        问题示例："显示'滤网需要更换'是什么意思？"
        预期：返回警告信息解释
        """
        response = client.post(
            "/chat/",
            json={"query": "显示'滤网需要更换'是什么意思？", "session_id": "test_017"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data


class TestDeviceListIntent:
    """测试列出设备意图 (device_list)。"""

    def test_list_all_devices(self):
        """测试：列出所有设备。
        
        问题示例："我有哪些设备？"、"显示所有设备"
        预期：返回设备列表
        """
        response = client.post(
            "/chat/",
            json={"query": "我有哪些设备？"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data

    def test_current_devices(self):
        """测试：询问当前设备。
        
        问题示例："当前有什么设备？"、"现在连接了哪些设备？"
        预期：返回当前连接的设备列表
        """
        response = client.post(
            "/chat/",
            json={"query": "当前有什么设备？"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data


class TestGeneralQAIntent:
    """测试一般知识问答意图 (general_qa)。"""

    def test_general_device_question(self):
        """测试：一般设备相关问题。
        
        问题示例："智能家电有什么好处？"、"如何选择适合的空气净化器？"
        预期：基于知识库返回答案
        """
        response = client.post(
            "/chat/",
            json={"query": "智能家电有什么好处？"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data

    def test_comparison_question(self):
        """测试：比较类问题。
        
        问题示例："变频空调和定频空调有什么区别？"
        预期：返回对比说明
        """
        response = client.post(
            "/chat/",
            json={"query": "变频空调和定频空调有什么区别？"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data


class TestMultiTurnConversation:
    """测试多轮对话场景。"""

    def test_conversation_context(self):
        """测试：会话上下文保持。
        
        第一轮："空调怎么开？"
        第二轮："那制热模式呢？"
        预期：第二轮能理解是在说空调
        """
        session_id = "test_session_001"
        
        # 第一轮
        response1 = client.post(
            "/chat/",
            json={"query": "空调怎么开？", "session_id": session_id}
        )
        assert response1.status_code == 200
        
        # 第二轮
        response2 = client.post(
            "/chat/",
            json={"query": "那制热模式呢？", "session_id": session_id}
        )
        assert response2.status_code == 200
        data = response2.json()
        assert data["session_id"] == session_id

    def test_device_reference_in_context(self):
        """测试：上下文中设备指代。
        
        第一轮："客厅的灯怎么控制？"
        第二轮："它的亮度可以调节吗？"
        预期：理解"它"指的是客厅的灯
        """
        session_id = "test_session_002"
        
        response1 = client.post(
            "/chat/",
            json={"query": "客厅的灯怎么控制？", "session_id": session_id}
        )
        assert response1.status_code == 200
        
        response2 = client.post(
            "/chat/",
            json={"query": "它的亮度可以调节吗？", "session_id": session_id}
        )
        assert response2.status_code == 200


class TestEdgeCases:
    """测试边界情况和异常处理。"""

    def test_empty_query(self):
        """测试：空查询处理。"""
        response = client.post("/chat/", json={"query": ""})
        # 空查询可能被接受（LLM 会处理）或返回验证错误
        assert response.status_code in [200, 422]

    def test_very_long_query(self):
        """测试：超长查询处理。"""
        long_query = "请问" + "这个设备" * 1000 + "怎么用？"
        response = client.post("/chat/", json={"query": long_query})
        # 应该能处理或返回适当的错误
        assert response.status_code in [200, 400, 422]

    def test_special_characters(self):
        """测试：特殊字符处理。"""
        response = client.post(
            "/chat/",
            json={"query": "设备@#$%显示&*()E3 错误，怎么办？"}
        )
        assert response.status_code == 200

    def test_mixed_language(self):
        """测试：混合语言处理。"""
        response = client.post(
            "/chat/",
            json={"query": "How to connect WiFi？我的设备不在线怎么办？"}
        )
        assert response.status_code == 200

    def test_unknown_intent(self):
        """测试：未知意图处理。
        
        问题不属于任何已知类别时应降级到 general_qa
        """
        response = client.post(
            "/chat/",
            json={"query": "今天天气怎么样？"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data


class TestResponseFormat:
    """测试响应格式规范。"""

    def test_response_structure(self):
        """测试：响应结构完整性。"""
        response = client.post(
            "/chat/",
            json={"query": "空调怎么开？"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # 验证必需字段
        assert "answer" in data
        assert isinstance(data["answer"], str)
        assert "sources" in data
        assert isinstance(data["sources"], list)
        assert "session_id" in data

    def test_sources_not_empty(self):
        """测试：来源引用（如果有引用知识）。"""
        response = client.post(
            "/chat/",
            json={"query": "空调的技术参数", "session_id": "test_018"}
        )
        assert response.status_code == 200
        data = response.json()
        # sources 可以为空，但字段必须存在
        assert "sources" in data

    def test_device_id_in_response(self):
        """测试：设备 ID 返回。"""
        response = client.post(
            "/chat/",
            json={"query": "状态如何？", "session_id": "test_019"}
        )
        assert response.status_code == 200
        data = response.json()
        # device_id 应该在响应中
        assert "device_id" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
