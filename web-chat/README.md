# 智能家居助手 Web 界面

一个现代化的 Web 聊天界面，用于与智能家居问答系统交互。

## 功能特性

- 实时聊天界面
- 可配置 API 地址、设备 ID 和设备类型
- 响应式设计，支持移动端
- 本地存储聊天历史和设置
- 设置面板可折叠
- 一键清空聊天历史
- 支持多行输入（Shift+Enter 换行）

## 快速开始

Web 聊天界面由 FastAPI 后端以静态文件方式托管，无需单独部署。

启动后端服务后，访问 `http://localhost:8000` 即可使用。

```bash
# 在项目根目录
./run.sh
```

## 项目结构

```
web-chat/
├── index.html      # 主页面
├── style.css       # 样式文件
├── app.js          # 应用逻辑
└── README.md       # 本文档
```

## 本地存储键值

- `apiBase`: API 地址
- `deviceId`: 设备 ID
- `deviceType`: 设备类型
- `sessionId`: 会话 ID
- `chatMessages`: 聊天历史（JSON）

## API 接口

向 `/chat/` 发送 POST 请求：

```json
{
  "query": "如何清洁冰箱？",
  "device_id": "optional-device-id",
  "device_type": "refrigerator",
  "session_id": "session-uuid"
}
```

响应格式：
```json
{
  "answer": "清洁冰箱的步骤...",
  "sources": ["文档1.pdf", "手册2.docx"],
  "device_id": "device-id",
  "session_id": "session-uuid"
}
```