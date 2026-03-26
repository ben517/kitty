"""Device Information Agent – handles device-related queries via API + RAG."""

from __future__ import annotations

import json
import logging
import re
from typing import Optional

from app.api.smartthings import smartthings, SmartThingsAPIError, RateLimitError, InvalidRequestError, AuthenticationError
from app.models.schemas import IntentType
from app.rag.generator import generate_answer
from app.rag.reranker import rerank
from app.rag.retriever import multi_recall

logger = logging.getLogger(__name__)

# UUID pattern for validation
_UUID_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE
)

# Mapping of SmartThings capability IDs to user-friendly Chinese descriptions
_CAPABILITY_DESCRIPTIONS = {
    # Basic capabilities
    "ocf": "OCF 连接协议",
    "switch": "开关控制",
    "refresh": "刷新状态",
    "execute": "执行命令",
    "logTrigger": "日志触发",
    "bypassable": "可旁路模式",
    "audioNotification": "音频通知",
    
    # Air conditioner specific
    "airConditionerMode": "空调模式设置（制冷/制热/送风等）",
    "airConditionerFanMode": "空调风扇模式设置",
    "fanOscillationMode": "风扇摆动模式",
    "temperatureMeasurement": "温度测量",
    "thermostatCoolingSetpoint": "冷却温度设定",
    "relativeHumidityMeasurement": "湿度测量",
    
    # Sensor capabilities
    "airQualitySensor": "空气质量传感器",
    "odorSensor": "气味传感器",
    "dustSensor": "灰尘传感器",
    "veryFineDustSensor": "细灰尘传感器 (PM2.5)",
    
    # Power and audio
    "audioVolume": "音量控制",
    "powerConsumptionReport": "功耗报告",
    "demandResponseLoadControl": "需求响应负载控制",
    
    # Custom capabilities
    "custom.spiMode": "SPI 模式",
    "custom.thermostatSetpointControl": "恒温器设定点控制",
    "custom.airConditionerOptionalMode": "可选空调模式",
    "custom.airConditionerTropicalNightMode": "热带夜晚模式",
    "custom.autoCleaningMode": "自动清洁模式",
    "custom.deviceReportStateConfiguration": "设备状态报告配置",
    "custom.energyType": "能源类型",
    "custom.dustFilter": "灰尘过滤器",
    "custom.veryFineDustFilter": "细灰尘过滤器 (PM2.5)",
    "custom.deodorFilter": "除臭过滤器",
    "custom.electricHepaFilter": "电动 HEPA 过滤器",
    "custom.doNotDisturbMode": "勿扰模式",
    "custom.periodicSensing": "周期感应",
    "custom.airConditionerOdorController": "空调气味控制器",
    "custom.disabledCapabilities": "禁用功能",
    
    # Samsung CE (Consumer Electronics) capabilities
    "samsungce.airConditionerAudioFeedback": "空调音频反馈",
    "samsungce.airConditionerBeep": "提示音",
    "samsungce.airConditionerDisplay": "显示屏控制",
    "samsungce.airConditionerLighting": "照明控制",
    "samsungce.airQualityHealthConcern": "空气质量健康关注",
    "samsungce.alwaysOnSensing": "始终感应",
    "samsungce.powerSavingWhileAway": "离家节能模式",
    "samsungce.softwareUpdate": "软件更新",
    "samsungce.softwareVersion": "软件版本",
    "samsungce.driverVersion": "驱动版本",
    "samsungce.dustFilterAlarm": "灰尘过滤器警报",
    "samsungce.deviceIdentification": "设备识别",
    "samsungce.quickControl": "快速控制",
    "samsungce.selfCheck": "自检功能",
    "samsungce.silentAction": "静音操作",
    "samsungce.unavailableCapabilities": "不可用功能",
    
    # SEC (Samsung Electronics) capabilities
    "sec.diagnosticsInformation": "诊断信息",
    "sec.wifiConfiguration": "WiFi 配置",
    "sec.calmConnectionCare": "稳定连接保护",
}


def _format_capabilities(capabilities_data: dict) -> str:
    """Convert raw capability data into user-friendly descriptions."""
    cap_lines = []
    for comp in capabilities_data.get("components", []):
        for cap in comp.get("capabilities", []):
            cap_id = cap.get("id", "")
            # Use mapping if available, otherwise use the raw ID
            description = _CAPABILITY_DESCRIPTIONS.get(cap_id, cap_id)
            cap_lines.append(f"- {description}")
    return "\n".join(cap_lines) if cap_lines else "无"


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

        # --- Auto-resolve device_id from device_type or device_id (if it's a name) ---
        # First try to resolve from device_type
        if not device_id and device_type:
            device_id = await self._resolve_device_id(device_type)
            if device_id:
                logger.info("Resolved device_id %s from device_type %s", device_id, device_type)
        # If device_id looks like a Chinese name (not a UUID), resolve it
        elif device_id and not self._is_uuid(device_id):
            resolved_id = await self._resolve_device_id(device_id)
            if resolved_id:
                logger.info("Resolved device_id %s from device name %s", resolved_id, device_id)
                device_id = resolved_id

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

    async def _resolve_device_id(self, device_type: str) -> Optional[str]:
        """Find device_id by matching device_type with SmartThings device categories."""
        try:
            data = await smartthings.get_devices()
            items = data.get("items", [])

            # Map Chinese device_type to possible English category names
            type_mapping = {
                "空调": ["Air Conditioner", "AirConditioner", "Thermostat"],
                "冰箱": ["Refrigerator", "Fridge"],
                "洗衣机": ["Washer", "Washing Machine"],
                "电视": ["TV", "Television"],
                "灯": ["Light", "Switch"],
            }
            possible_names = type_mapping.get(device_type, [device_type])

            for device in items:
                components = device.get("components", [])
                for comp in components:
                    categories = comp.get("categories", [])
                    for cat in categories:
                        cat_name = cat.get("name", "")
                        for possible in possible_names:
                            if possible.lower() in cat_name.lower():
                                return device.get("deviceId")

                # Also check device label/name
                label = device.get("label") or device.get("name", "")
                if device_type in label:
                    return device.get("deviceId")

            return None
        except RateLimitError as e:
            logger.warning("Rate limit exceeded while resolving device_id for %s: %s", device_type, e)
            return None
        except InvalidRequestError as e:
            logger.warning("Invalid request when resolving device_id for %s: %s (likely invalid device name)", device_type, e)
            return None
        except AuthenticationError as e:
            logger.error("Authentication failed when resolving device_id: %s", e)
            return None
        except SmartThingsAPIError as e:
            logger.warning("Failed to resolve device_id for %s: %s", device_type, e)
            return None
        except Exception:
            logger.warning("Failed to resolve device_id for %s", device_type, exc_info=True)
            return None

    @staticmethod
    def _is_uuid(value: str) -> bool:
        """Check if a string looks like a UUID."""
        return bool(_UUID_PATTERN.match(value))

    async def _handle_device_list(self, query: str) -> dict:
        """Fetch all devices and summarize with LLM."""
        try:
            # Fetch both devices and rooms
            devices_data = await smartthings.get_devices()
            rooms_data = await smartthings.get_rooms()
            
            items = devices_data.get("items", [])
            rooms = rooms_data.get("items", [])
            
            # Build room_id -> room_name mapping
            room_map = {}
            for room in rooms:
                room_id = room.get("roomId")
                room_name = room.get("name", "未知房间")
                room_map[room_id] = room_name
            
            device_lines = []
            for d in items:
                label = d.get("label") or d.get("name", "未知设备")
                category = ""
                components = d.get("components", [])
                if components:
                    cats = components[0].get("categories", [])
                    if cats:
                        category = cats[0].get("name", "")
                
                # Get room information
                room_id = d.get("roomId")
                room_name = room_map.get(room_id, "未知位置") if room_id else "未分配房间"
                
                device_lines.append(f"- {label}（{category}，位于{room_name}，ID: {d['deviceId']}）")
            
            device_summary = "\n".join(device_lines) if device_lines else "未找到任何设备"
            extra_context = f"当前账号下共有 {len(items)} 台设备：\n{device_summary}"
        except RateLimitError as e:
            logger.warning("Rate limit exceeded when fetching device list: %s", e)
            extra_context = "无法获取设备列表：API 请求过于频繁，请稍后重试。"
        except AuthenticationError as e:
            logger.error("Authentication failed when fetching device list: %s", e)
            extra_context = "无法获取设备列表：SmartThings Token 已过期或无效。请重新生成 Personal Access Token (PAT) 并更新到 .env 文件中。（PAT 有效期为 24 小时）"
        except SmartThingsAPIError as e:
            logger.warning("Failed to fetch device list: %s", e)
            extra_context = f"无法获取设备列表：{e}"
        except Exception as e:
            logger.warning("Failed to fetch device list: %s", e, exc_info=True)
            error_msg = str(e)
            if "401" in error_msg or "Unauthorized" in error_msg:
                extra_context = "无法获取设备列表：SmartThings Token 已过期或无效。请重新生成 Personal Access Token (PAT) 并更新到 .env 文件中。（PAT 有效期为 24 小时）"
            elif "Event loop is closed" in error_msg or "async" in error_msg.lower():
                # Async event loop issue - provide user-friendly message
                extra_context = "无法获取设备列表：当前系统事件循环已关闭。请尝试重新启动服务后再次查询。"
            else:
                extra_context = f"无法获取设备列表：{error_msg}"

        answer = generate_answer(query, [], extra_context=extra_context)
        return {"answer": answer, "sources": [], "device_id": None}

    async def _fetch_device_context(self, intent: IntentType, device_id: str) -> str:
        """Fetch real-time device information from SmartThings API."""
        try:
            # Fetch basic device info first (contains roomId, model, etc.)
            device_data = await smartthings.get_device(device_id)
            
            # Extract key device info
            device_name = device_data.get("label") or device_data.get("name", "未知设备")
            # Try multiple fields for model information
            device_model = (device_data.get("model") 
                           or device_data.get("presentationId") 
                           or device_data.get("deviceTypeName") 
                           or "")
            manufacturer = device_data.get("manufacturerName", "")
            
            # Get room name from roomId
            room_name = "未知位置"
            room_id = device_data.get("roomId")
            if room_id:
                try:
                    rooms_data = await smartthings.get_rooms()
                    for room in rooms_data.get("items", []):
                        if room.get("roomId") == room_id:
                            room_name = room.get("name", "未知房间")
                            break
                except Exception:
                    logger.warning("Failed to fetch room info for device %s", device_id, exc_info=True)
            
            context_parts = [
                f"设备名称：{device_name}",
                f"设备位置：位于{room_name}",
            ]
            if device_model:
                context_parts.append(f"设备型号/标识：{device_model}")
            if manufacturer:
                context_parts.append(f"制造商：{manufacturer}")
            
            if intent == IntentType.DEVICE_STATUS:
                status_data = await smartthings.get_device_status(device_id)
                context_parts.append(f"当前状态：{json.dumps(status_data, ensure_ascii=False)}")
            
            elif intent == IntentType.DEVICE_SIGNAL:
                health_data = await smartthings.get_device_health(device_id)
                context_parts.append(f"健康状态：{json.dumps(health_data, ensure_ascii=False)}")
            
            elif intent == IntentType.TECH_PARAM:
                capabilities_data = await smartthings.get_device_capabilities(device_id)
                # Format capabilities with user-friendly descriptions
                formatted_caps = _format_capabilities(capabilities_data)
                context_parts.append(f"支持的功能:\n{formatted_caps}")
            
            else:
                context_parts.append(f"详细信息：{json.dumps(device_data, ensure_ascii=False)}")
            
            return "\n".join(context_parts)

        except RateLimitError as e:
            logger.warning("Rate limit exceeded when fetching device info for %s: %s", device_id, e)
            return ""
        except InvalidRequestError as e:
            logger.warning("Invalid request when fetching device info for %s: %s (device ID may be invalid)", device_id, e)
            return ""
        except AuthenticationError as e:
            logger.error("Authentication failed when fetching device info: %s", e)
            return ""
        except SmartThingsAPIError as e:
            logger.warning("Failed to fetch device info for %s: %s", device_id, e)
            return ""
        except Exception:
            logger.warning("Failed to fetch device info for %s", device_id, exc_info=True)
            return ""


device_info_agent = DeviceInfoAgent()
