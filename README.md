1.项目概述
本项目旨在构建一个面向家用电器设备的智能问答系统，通过集成本地RAG（Retrieval-Augmented Generation)技术和多Agent协作架构，为用户提供准确快速的设备相关信息查询服务。

2.核心组件架构
2.1 设备知识库构建模块
2.1.1 数据采集：设备说明书
2.1.2 数据处理流程
1.文档解析（PDF/Word/HTML)
2.文本清洗和分段
3.向量化处理
4.数据库存储

2.2 本地RAG构建模块
2.2.1 检索优化
  多路召回：关键词检索+语义检索
  重排序：基于相关性评分的重排序
  过滤机制：设备类型过滤+时效性过滤
2.2.2 生成优化
  上下文管理：动态上下文长度调整
  后处理：答案格式化+可读性优化
2.3 主编排Agent模块
2.3.1 意图识别
  多Agent路由策略
  优先级调度
  负载均衡
2.3.2 结果融合
  多源信息整合
  冲突解决机制
2.4 设备信息Agent模块
2.4.1 核心功能
  设备状态查询
  设备信号识别
  技术参数查询
  操作步骤指导
  故障代码解释
2.4.2 交换设计
  多轮对话支持
  上下文理解
  模糊查询处理

3.API
应用场景：用户涉及到查询自己的相关设备时调用，由设备信息Agent模块调用
基础URL和头部设置
BASE_API_URL="https://api.samsungiotcloud.cn"
认证头部
AUTH_HEADER="Authorization: Bearer YOUR_PAT_TKONE"
CONTENT_TYPE_HEADER="Content-Type: application/json"
3.1 设备管理相关API
获取房间列表 
get /locations/YOUR_LOCATION_ID/rooms
获取设备列表
get /devices?locationId=YOUR_LOCATION_ID
获取指定设备信息
get /device/YOUR_DEVICE_ID
获取设备状态
get /devices/YOUR_DEVICE_ID/statis
获取设备健康状态
get /devices/YOUR_DEVICE_ID/health
获取设备能力信息
get /devices/YOUR_DEVICE_ID/capabilities
批量查询设备能力
post /capabilities/query
body:
{
  "query": [
    {
      "id": "swith",
      "version": 1
    },
    {
      "id": "switchLevel",
      "version": 1
    }
  ]
}

4.核心使用框架
langchain
chroma
LLM:qwen
Embedding:qwen3-embedding
