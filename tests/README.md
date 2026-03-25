# 测试框架总览

本项目采用双层测试架构：**单元测试** + **场景化测试**，确保代码质量和系统稳定性。

## 📁 目录结构

```
tests/
├── __init__.py
├── unit/                          # 单元测试 (~100 个用例)
│   ├── __init__.py
│   ├── test_schemas.py            # Pydantic 模型验证 (24 用例)
│   ├── test_chat_intents.py       # API 集成测试 (35+ 用例)
│   ├── test_device_endpoints.py   # 设备端点测试 (20+ 用例)
│   └── test_knowledge_upload.py   # 知识上传测试 (20+ 用例)
└── scenarios/                     # 场景化测试 (49 个场景)
    ├── __init__.py
    ├── test_runner.py             # 统一测试执行器 ⭐
    ├── test_scenarios_input.yaml  # YAML 配置文件 ⭐
    └── output/                    # 输出目录（仅 Excel）
```

## 🚀 快速开始

### 运行所有单元测试

```bash
pytest tests/unit/ -v
```

### 运行场景化测试

```bash
# 确保服务已启动
./run.sh &

# 运行所有场景测试（生成 Excel 报告）
python tests/scenarios/test_runner.py
```

### 查看测试结果

测试完成后，Excel 报告会生成在项目根目录的 `output/` 文件夹：

```bash
ls -la output/test_*.xlsx
```

## 📊 测试覆盖对比

| 特性 | 单元测试 | 场景化测试 |
|------|---------|-----------|
| **位置** | `tests/unit/` | `tests/scenarios/` |
| **用例数** | ~100 | 49 |
| **目的** | 验证代码逻辑正确性 | 模拟真实用户场景 |
| **范围** | 单个函数/类/端点 | 完整业务流程 |
| **速度** | 快 (<1s/个) | 较慢 (含 LLM 调用) |
| **依赖** | 无或很少 | 需要运行的服务 |
| **执行方式** | pytest | Python 脚本 |
| **输出** | 控制台 | Excel 报告 |

## 📝 单元测试 (tests/unit/)

验证代码的各个组成部分是否正常工作。

### 文件说明

| 文件 | 用例数 | 说明 |
|------|--------|------|
| `test_schemas.py` | 24 | Pydantic 模型验证 |
| `test_chat_intents.py` | 35+ | `/chat/` 端点集成测试 |
| `test_device_endpoints.py` | 20+ | SmartThings API 代理测试 |
| `test_knowledge_upload.py` | 20+ | 文档上传处理测试 |

**总计**: ~100 个测试用例

### 测试类型

#### 1. Schema 验证测试 (`test_schemas.py`)

验证 Pydantic 数据模型的正确性：
- `ChatRequest` - 请求参数验证
- `ChatResponse` - 响应格式验证
- `IntentType` - 枚举类型验证（7 种意图）
- `IntentResult` - 意图识别结果验证
- `DeviceInfo/Status/Health` - 设备相关模型验证
- `DocumentUploadResponse` - 上传响应验证

#### 2. API 集成测试 (`test_chat_intents.py`)

测试 `/chat/` 端点的各种场景：
- **DEVICE_STATUS** (5 个) - 设备状态查询
- **DEVICE_SIGNAL** (4 个) - 设备信号/健康
- **TECH_PARAM** (7 个) - 技术参数查询
- **OPERATION_GUIDE** (5 个) - 操作步骤指导
- **FAULT_CODE** (4 个) - 故障代码解释
- **DEVICE_LIST** (3 个) - 设备列表查询
- **GENERAL_QA** (3 个) - 一般知识问答
- **多轮对话** (2 个) - 上下文理解
- **边界情况** (5 个) - 异常处理

#### 3. 设备端点测试 (`test_device_endpoints.py`)

测试 SmartThings API 代理端点：
- `GET /devices/` - 获取设备列表
- `GET /devices/{id}` - 获取设备详情
- `GET /devices/{id}/status` - 获取设备状态
- `GET /devices/{id}/health` - 获取健康状态
- `GET /devices/{id}/capabilities` - 获取设备能力

#### 4. 知识上传测试 (`test_knowledge_upload.py`)

测试文档上传和处理功能：
- 支持格式：PDF, TXT, DOCX, HTML
- 参数验证：device_type 必需
- 边界情况：空文件、大文件、特殊字符
- 并发上传：多线程测试

### 常用命令

```bash
# 运行所有单元测试
pytest tests/unit/ -v

# 运行特定测试文件
pytest tests/unit/test_schemas.py -v
pytest tests/unit/test_chat_intents.py -v
pytest tests/unit/test_device_endpoints.py -v
pytest tests/unit/test_knowledge_upload.py -v

# 运行特定测试类
pytest tests/unit/test_schemas.py::TestChatRequestSchema -v
pytest tests/unit/test_chat_intents.py::TestDeviceStatusIntent -v

# 生成覆盖率报告
pytest tests/unit/ --cov=app --cov-report=html
pytest tests/unit/ --cov=app --cov-report=term-missing

# 快速运行（失败即停）
pytest tests/unit/ -x

# 只看失败的测试
pytest tests/unit/ --lf
```

### 与场景测试的区别

| 特性 | 单元测试 | 场景测试 |
|------|---------|---------|
| 位置 | `tests/unit/` | `tests/scenarios/` |
| 目的 | 验证代码逻辑正确性 | 模拟真实用户场景 |
| 范围 | 单个函数/类/端点 | 完整的业务流程 |
| 执行速度 | 快 (<1s/个) | 较慢（涉及 LLM 调用） |
| 依赖 | 少或无 | 需要运行的服务 |
| 用例数 | ~100 个 | 44 个场景 |

### 何时添加单元测试

- ✅ 新增 Pydantic 模型时 → `test_schemas.py`
- ✅ 修改 API 端点逻辑时 → 对应的 `test_*.py`
- ✅ 发现 Bug 时 → 添加回归测试
- ✅ 重构代码时 → 确保现有测试通过

### 注意事项

- ✅ 单元测试应该独立：每个测试不依赖其他测试的状态
- ✅ 使用 mock：对于外部依赖（如 LLM），考虑使用 mock
- ✅ 快速执行：单元测试应该快速完成（< 1 秒/个）
- ✅ 明确断言：每个测试应该有清晰的验证逻辑

## 🎯 场景化测试 (tests/scenarios/)

基于真实用户场景的端到端测试，验证整个系统的行为。

### 文件说明

| 文件 | 说明 |
|------|------|
| `test_runner.py` | **统一测试执行器** - 执行所有测试并生成 Excel 报告 ⭐ |
| `test_scenarios_input.yaml` | **YAML 配置文件** - 定义所有测试场景（49 个） ⭐ |

### 场景分类

| 类别 | 场景数 | 示例问题 |
|------|--------|---------|
| 设备状态查询 | 6 | "空调现在开着吗？"、"空调在哪个房间？" |
| 设备信号/健康 | 4 | "设备是否在线？" |
| 技术参数查询 | 9 | "这款冰箱的容量是多少？"、"我的空调是什么型号？"、"我的空调有哪些能力？" |
| 操作步骤指导 | 8 | "怎么设置定时？" |
| 故障代码解释 | 5 | "E3 是什么故障？" |
| 设备列表查询 | 5 | "我有哪些设备？"、"我名下有空调吗？"、"我的客厅有哪些设备？" |
| 一般知识问答 | 4 | "变频和定频空调有什么区别？" |
| 多轮对话 | 4 (2 组) | "空调怎么开？→ 那制热呢？" |
| 边界情况 | 4 | "今天天气怎么样？" |

### 常用命令

```bash
# 运行完整测试（生成 Excel 报告到 output/）
python tests/scenarios/test_runner.py

# 查看最新 Excel 报告
ls -la output/test_*.xlsx
```

### Excel 报告内容

生成的 Excel 报告包含以下列：

1. **场景 ID** - 测试用例编号
2. **类别** - 意图类型分类
3. **场景描述** - 测试场景说明
4. **输入问题** - 用户查询
5. **实际回答** - LLM 返回的完整回答
6. **响应时间 (ms)** - 总响应时间
7. **LLM 时间 (ms)** - LLM 调用耗时
8. **预期意图** - 期望的意图类型
9. **实际意图** - 系统识别的意图
10. **结果** - 意图匹配是否正确
11. **优先级** - 测试优先级
12. **状态码** - HTTP 状态码
13. **错误信息** - 错误详情

### 添加新测试场景

编辑 `test_scenarios_input.yaml` 文件，添加新的场景：

```yaml
scenarios:
  - category: your_category
    priority: high  # 或 medium, low
    scenes:
      - id: your_unique_id
        description: "场景描述"
        query: "用户会问的问题"
        expected_intent: operation_guide  # 预期的意图类型
        entities: {}
```

然后运行测试验证：

```bash
python tests/scenarios/test_runner.py
```

### 注意事项

- ⚠️ 需要运行 FastAPI 服务 (`./run.sh`)
- ⚠️ 配置正确的 LLM 和环境变量（从 `.env` 加载）
- ⚠️ 执行时间较长（约 3 秒/用例）
- ✅ 只生成 Excel 报告到 `output/` 目录

## 📈 测试报告

### 生成的文件

| 文件 | 说明 | 位置 |
|------|------|------|
| `test_YYYYMMDD_HHMMSS.xlsx` | **Excel 格式测试报告**（包含所有详细数据） | `output/` |

### 输出示例

```
============================================================
## 测试汇总报告
测试总数：49
成功：49
失败：0
成功率：100.0%
平均响应时间：3551.7 ms
Excel 报告已保存到：/workspaces/kitty/output/test_20260325_060256.xlsx
============================================================
```

### Excel 报告内容

打开 Excel 文件后，可以看到：
- **汇总统计** 工作表：总体统计、按优先级统计、按类别统计
- **测试结果** 工作表：每个测试用例的详细信息

## 🎯 推荐工作流

```
1. 开发新功能
   ↓
2. 编写单元测试 (tests/unit/)
   ↓
3. 验证单元测试通过
   ↓
4. 添加到场景测试 (tests/scenarios/test_scenarios_input.yaml)
   ↓
5. 运行场景测试验证整体功能
   ↓
6. 查看 Excel 报告分析结果
```

## 🔧 配置说明

### 环境变量

测试可能需要以下环境变量（从 `.env` 文件加载）：

```bash
LLM_MODEL=openai/qwen-turbo
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_API_KEY=your_api_key
```

## 📚 相关文档

| 文档 | 位置 | 适合人群 |
|------|------|---------|
| `tests/unit/README.md` | tests/unit/ | 单元测试开发者 |
| `tests/README.md` | tests/ | 测试框架总览（本文档） |

## ⚠️ 注意事项

### 单元测试
- ✅ 保持测试独立性
- ✅ 使用 mock 隔离外部依赖
- ✅ 快速执行
- ✅ 明确的断言

### 场景化测试
- ⚠️ 需要运行的 FastAPI 服务
- ⚠️ 配置正确的 LLM 和环境变量
- ⚠️ 执行时间较长（约 3 秒/用例）
- ⚠️ 关注趋势而非单次数值
- ✅ **只生成 Excel 报告**，简洁明了

## 🤝 贡献指南

### 添加新测试

1. **单元测试**: 在 `tests/unit/` 对应文件中添加
2. **场景测试**: 在 `tests/scenarios/test_scenarios_input.yaml` 中添加场景数据
3. **更新文档**: 更新本 README 文件

### 测试命名规范

- 单元测试：`test_<functionality>.py`
- 场景测试：使用有意义的 ID，如 `ds_001` (device_status_001)

---

**最后更新**: 2026-03-25  
**维护**: Qoder Team
