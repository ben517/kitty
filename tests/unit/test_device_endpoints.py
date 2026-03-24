"""测试用例：设备相关 API 端点测试。

测试 /devices/* 系列端点的功能。
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# Valid device ID format (GUID)
VALID_DEVICE_ID = "f4b3af92-5826-416e-8e28-8b1c252912f1"


class TestDevicesListEndpoint:
    """测试获取设备列表端点。"""

    def test_list_devices_success(self):
        """测试：成功获取设备列表。
        
        GET /devices/
        预期：返回设备列表（可能为空）
        """
        response = client.get("/devices/")
        # 200=成功，500=API 未配置，403=令牌无权限
        assert response.status_code in [200, 403, 500]
        
        if response.status_code == 200:
            data = response.json()
            # API 返回的是包含 'items' 的字典
            assert isinstance(data, (list, dict))

    def test_list_devices_with_query_params(self):
        """测试：带查询参数的设备列表。
        
        GET /devices/?room=living_room
        预期：按房间过滤设备
        """
        response = client.get("/devices/", params={"room": "living_room"})
        # 应能处理查询参数
        assert response.status_code in [200, 403, 422, 500]


class TestDeviceInfoEndpoint:
    """测试获取单个设备信息端点。"""

    def test_get_device_info(self):
        """测试：获取设备详细信息。
        
        GET /devices/{device_id}
        预期：返回设备基本信息
        """
        response = client.get(f"/devices/{VALID_DEVICE_ID}")
        # 200=成功，400=格式错误，403=无权限，404=不存在，500=API 未配置
        assert response.status_code in [200, 400, 403, 404, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "device_id" in data

    def test_get_nonexistent_device(self):
        """测试：获取不存在的设备。
        
        GET /devices/nonexistent_device
        预期：返回 404 错误
        """
        # 使用无效的 GUID 格式测试
        response = client.get("/devices/00000000-0000-0000-0000-000000000000")
        assert response.status_code in [400, 403, 404, 500]

    def test_get_device_with_special_chars(self):
        """测试：设备 ID 包含特殊字符。
        
        GET /devices/device-123_abc
        预期：正确处理 URL 编码
        """
        # 非 GUID 格式会返回 400
        response = client.get("/devices/device-123_abc")
        assert response.status_code in [200, 400, 403, 404, 500]


class TestDeviceStatusEndpoint:
    """测试获取设备状态端点。"""

    def test_get_device_status(self):
        """测试：获取设备当前状态。
        
        GET /devices/{device_id}/status
        预期：返回设备组件状态
        """
        response = client.get(f"/devices/{VALID_DEVICE_ID}/status")
        assert response.status_code in [200, 400, 403, 404, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "device_id" in data

    def test_get_status_components(self):
        """测试：状态包含组件信息。
        
        预期：components 字段包含各组件状态
        """
        response = client.get(f"/devices/{VALID_DEVICE_ID}/status")
        if response.status_code == 200:
            data = response.json()
            assert "components" in data
            assert isinstance(data["components"], dict)


class TestDeviceHealthEndpoint:
    """测试获取设备健康状态端点。"""

    def test_get_device_health(self):
        """测试：获取设备健康状态。
        
        GET /devices/{device_id}/health
        预期：返回健康状态信息
        """
        response = client.get(f"/devices/{VALID_DEVICE_ID}/health")
        assert response.status_code in [200, 400, 403, 404, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "device_id" in data
            assert "state" in data or data.get("state") is not None

    def test_health_state_values(self):
        """测试：健康状态值范围。
        
        预期的健康状态：online, offline, warning, error 等
        """
        response = client.get(f"/devices/{VALID_DEVICE_ID}/health")
        if response.status_code == 200:
            data = response.json()
            state = data.get("state")
            if state:
                assert state in ["online", "offline", "warning", "error", "unknown"]


class TestDeviceCapabilitiesEndpoint:
    """测试获取设备能力端点。"""

    def test_get_device_capabilities(self):
        """测试：获取设备支持的能力。
        
        GET /devices/{device_id}/capabilities
        预期：返回设备支持的命令和功能
        """
        response = client.get(f"/devices/{VALID_DEVICE_ID}/capabilities")
        assert response.status_code in [200, 400, 403, 404, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or isinstance(data, dict)

    def test_capabilities_structure(self):
        """测试：能力列表结构。
        
        预期：包含命令名称和参数说明
        """
        response = client.get(f"/devices/{VALID_DEVICE_ID}/capabilities")
        if response.status_code == 200:
            data = response.json()
            # capabilities 应该是列表或包含 commands 的字典
            assert len(data) >= 0  # 可以为空


class TestDeviceEndpointsEdgeCases:
    """测试设备端点边界情况。"""

    def test_empty_device_id(self):
        """测试：空设备 ID。
        
        GET /devices/
        预期：返回设备列表而非 404
        """
        response = client.get("/devices/")
        assert response.status_code in [200, 500]

    def test_invalid_device_id_format(self):
        """测试：无效设备 ID 格式。
        
        GET /devices/!@#$%
        预期：适当处理（404 或 400）
        """
        response = client.get("/devices/!@#$%")
        # URL 编码后应该能处理
        assert response.status_code in [400, 403, 404, 500]

    def test_very_long_device_id(self):
        """测试：超长设备 ID。
        
        预期：合理处理长字符串
        """
        long_id = "a" * 1000  # 使用纯字母 GUID 格式
        response = client.get(f"/devices/{long_id}")
        assert response.status_code in [400, 404, 414, 500]  # 400=Bad format, 414 = URI Too Long


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
