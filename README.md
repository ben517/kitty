# SOS Demo 项目概述

本项目旨在构建一个面向家用电器设备的智能问答系统，通过集成本地 RAG（Retrieval-Augmented Generation）技术和多 Agent 协作架构，为用户提供准确、快速的设备相关信息查询服务。

---

## 快速开始

### 1. 环境准备

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装依赖（已预装）
pip install -r requirements.txt
```

### 2. 配置环境变量

复制配置模板并填写必要参数：

```bash
cp .env.example .env
```

编辑 `.env` 文件，至少需要配置 DashScope API 密钥：

```bash
# LLM 配置（使用阿里通义千问）
SOS_LLM_MODEL=openai/qwen-turbo
SOS_LLM_API_KEY=sk-xxxxxxxxxxxx  # 你的 DashScope API Key
SOS_LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# Embedding 配置
SOS_EMBEDDING_MODEL=openai/text-embedding-v3
SOS_EMBEDDING_API_KEY=sk-xxxxxxxxxxxx  # 同上
SOS_EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# SmartThings API（可选）
SOS_SMARTTHINGS_TOKEN=your_pat_token_here
SOS_SMARTTHINGS_LOCATION_ID=your_location_id
```

### 3. 启动服务

```bash
# 方法一：使用启动脚本（推荐）
./run.sh

# 方法二：手动启动
LD_LIBRARY_PATH=/nix/store/03h8f1wmpb86s9v8xd0lcb7jnp7nwm6l-idx-env-fhs/usr/lib:$LD_LIBRARY_PATH \
  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后访问：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

---

## 核心功能使用

### 1. 上传设备说明书

将设备手册（PDF/Word/HTML/TXT）上传到知识库：

```bash
curl -X POST http://localhost:8000/knowledge/upload \
  -F "file=@空调使用说明书.pdf" \
  -F "device_type=空调"
```

### 2. 智能问答

通过 `/chat/` 接口进行设备相关问答：

```bash
curl -X POST http://localhost:8000/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "空调怎么连WiFi？",
    "device_type": "空调"
  }'
```

支持的意图类型：
- 设备状态查询（"空调现在开着吗"）
- 技术参数查询（"这款冰箱的容量是多少"）
- 操作步骤指导（"怎么设置定时"）
- 故障代码解释（"E3是什么故障"）
- 一般知识问答

### 3. 查询设备实时信息（需配置 SmartThings）

```bash
# 获取设备列表
curl http://localhost:8000/devices/

# 获取特定设备状态
curl http://localhost:8000/devices/{device_id}/status

# 获取设备健康状态
curl http://localhost:8000/devices/{device_id}/health
```

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
  GET /devices/YOUR_DEVICE_ID/status
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
        "id": "switch",
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
- LLM: qwen (via litellm)
- Embedding: qwen3-embedding
- python
