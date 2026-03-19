# SOS Demo 项目概述

本项目旨在构建一个面向家用电器设备的智能问答系统，通过集成本地 RAG（Retrieval-Augmented Generation）技术和多 Agent 协作架构，为用户提供准确、快速的设备相关信息查询服务。

---

## 1. 核心组件架构

### 1.1 设备知识库构建模块

- **数据采集**：设备说明书
- **数据处理流程**：
  1. 文档解析（PDF/Word/HTML）
  2. 文本清洗和分段
  3. 向量化处理
  4. 数据库存储

### 1.2 本地 RAG 构建模块

#### 1.2.1 检索优化
- 多路召回：关键词检索 + 语义检索
- 重排序：基于相关性评分的重排序
- 过滤机制：设备类型过滤 + 时效性过滤

#### 1.2.2 生成优化
- 上下文管理：动态上下文长度调整
- 后处理：答案格式化 + 可读性优化

### 1.3 主编排 Agent 模块

#### 1.3.1 意图识别
- 多 Agent 路由策略
- 优先级调度
- 负载均衡

#### 1.3.2 结果融合
- 多源信息整合
- 冲突解决机制

### 1.4 设备信息 Agent 模块

#### 1.4.1 核心功能
- 设备状态查询
- 设备信号识别
- 技术参数查询
- 操作步骤指导
- 故障代码解释

#### 1.4.2 交互设计
- 多轮对话支持
- 上下文理解
- 模糊查询处理

---

## 2. API（示例）

### 2.1 基本配置

- **基础 URL**：
  ```bash
  BASE_API_URL="https://api.samsungiotcloud.cn"
  ```

- **认证头部**：
  ```bash
  AUTH_HEADER="Authorization: Bearer YOUR_PAT_TKONE"
  CONTENT_TYPE_HEADER="Content-Type: application/json"
  ```

### 2.2 设备管理相关 API（示例）

- 获取房间列表
  ```http
  GET /locations/YOUR_LOCATION_ID/rooms
  ```

- 获取设备列表
  ```http
  GET /devices?locationId=YOUR_LOCATION_ID
  ```

- 获取指定设备信息
  ```http
  GET /device/YOUR_DEVICE_ID
  ```

- 获取设备状态
  ```http
  GET /devices/YOUR_DEVICE_ID/statis
  ```

- 获取设备健康状态
  ```http
  GET /devices/YOUR_DEVICE_ID/health
  ```

- 获取设备能力信息
  ```http
  GET /devices/YOUR_DEVICE_ID/capabilities
  ```

- 批量查询设备能力
  ```http
  POST /capabilities/query
  Content-Type: application/json
  
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
  ```

---

## 3. 核心使用框架

- langchain
- chroma
- LLM: qwen
- Embedding: qwen3-embedding
- TypeScript