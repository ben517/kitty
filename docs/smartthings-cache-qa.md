# SmartThings API 缓存机制问答

## Q1: SmartThings API 缓存是如何实现的？

缓存通过 `_TimedCache` 类实现，位于 `app/api/smartthings.py:17-58`。这是一个简单的内存缓存，支持 TTL（Time To Live）过期机制：

- 使用 `dict` 存储缓存数据，格式为 `{key: (value, expire_time)}`
- 使用 `asyncio.Lock` 保证并发安全
- 读取时自动检查过期时间，过期则自动删除
- 所有操作都带有 INFO 级别日志记录

```python
class _TimedCache:
    async def get(self, key: str) -> Any      # 获取缓存（过期自动删除，日志: [Cache] HIT/MISS/EXPIRED）
    async def set(self, key: str, value: Any, ttl: int)  # 设置缓存（日志: [Cache] SET）
    async def delete(self, key: str)          # 删除单个缓存（日志: [Cache] DELETE）
    async def clear(self)                     # 清空所有缓存（日志: [Cache] CLEAR）
```

---

## Q2: 涉及缓存的 API 有哪些？

| API 方法 | 对应端点 | 缓存时间 | 说明 |
|---------|---------|---------|------|
| `get_rooms()` | `/locations/{location_id}/rooms` | 300秒(5分钟) | 房间列表，很少变化 |
| `get_devices()` | `/devices` | 60秒 | 设备列表 |
| `get_device()` | `/devices/{device_id}` | 30秒 | 单个设备信息 |
| `get_device_status()` | `/devices/{device_id}/status` | 10秒 | 设备状态（频繁变化） |
| `get_device_health()` | `/devices/{device_id}/health` | 30秒 | 设备健康状态 |
| `get_device_capabilities()` | 内部调用 `get_device()` | 30秒 | 设备能力（复用设备信息缓存） |

**缓存时间配置常量**（`app/api/smartthings.py:92-98`）：

```python
CACHE_TTL_DEVICES = 60    # Device list cache for 60 seconds
CACHE_TTL_DEVICE = 30     # Single device info cache for 30 seconds
CACHE_TTL_STATUS = 10     # Device status cache for 10 seconds (changes frequently)
CACHE_TTL_HEALTH = 30     # Device health cache for 30 seconds
CACHE_TTL_ROOMS = 300     # Room list cache for 5 minutes (rarely changes)
```

---

## Q3: 缓存 Key 的格式是什么？

缓存 Key 由 `_make_cache_key()` 方法生成（`app/api/smartthings.py:128-136`）：

```
格式: {METHOD}:{PATH}?{sorted_params}

示例:
- GET:/devices?locationId=xxx-xxx-xxx
- GET:/devices/device-123
- GET:/devices/device-123/status
```

生成逻辑：
```python
def _make_cache_key(self, method: str, path: str, **kwargs) -> str:
    params = kwargs.get("params", {})
    params_str = ""
    if params:
        sorted_params = sorted(params.items())  # 参数排序保证一致性
        params_str = "?" + "&".join(f"{k}={v}" for k, v in sorted_params)
    return f"{method}:{path}{params_str}"
```

---

## Q4: 缓存 Value 存储的是什么？

缓存 Value 存储 API 响应的原始 JSON 数据（已解析为 Python dict）：

```python
result = resp.json() if resp.content else {}
await self._cache.set(cache_key, result, cache_ttl)
```

---

## Q5: 如何清理缓存？

### 方法一：调用 `clear_cache()` 清空所有缓存

```python
from app.api.smartthings import smartthings

# 清空所有缓存
await smartthings.clear_cache()
```

### 方法二：删除单个缓存 Key

```python
# 删除特定缓存
cache_key = "GET:/devices/device-123"
await smartthings._cache.delete(cache_key)
```

### 方法三：等待自动过期

缓存基于 TTL 自动过期，读取时会检查过期时间并自动删除过期数据。

---

## Q6: 缓存的工作流程是怎样的？

```
┌─────────────────────────────────────────────────────────────┐
│                      API 请求流程                            │
├─────────────────────────────────────────────────────────────┤
│  1. 生成缓存 Key: "GET:/devices/{id}"                        │
│                          │                                   │
│                          ▼                                   │
│  2. 检查是否使用缓存 (use_cache=True && method=GET && ttl>0)  │
│                          │                                   │
│              ┌───────────┴───────────┐                       │
│              ▼                       ▼                       │
│         缓存命中                  缓存未命中                   │
│              │                       │                       │
│              ▼                       ▼                       │
│     检查是否过期              执行实际 API 请求               │
│         ┌────┴────┐                  │                       │
│         ▼         ▼                  ▼                       │
│       未过期     已过期          存入缓存                      │
│         │         │                  │                       │
│         ▼         ┼──────────────────┘                       │
│     返回缓存值            返回响应数据                         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Q7: 为什么不同 API 使用不同的缓存时间？

缓存时间的设置基于数据变化频率：

| 数据类型 | 变化频率 | 缓存时间 | 设计考量 |
|---------|---------|---------|---------|
| 房间列表 | 很少变化 | 5分钟 | 房间配置稳定，长缓存减少 API 调用 |
| 设备列表 | 较少变化 | 60秒 | 新增/删除设备频率较低 |
| 设备信息 | 中等 | 30秒 | 设备名称、型号等信息相对稳定 |
| 设备状态 | 频繁变化 | 10秒 | 开关状态、温度等实时数据变化快 |
| 设备健康 | 中等 | 30秒 | 健康/离线状态不会频繁变化 |

---

## Q8: 缓存与限流是如何配合的？

SmartThings API 客户端同时实现了缓存和限流机制：

```python
# 限流配置 (app/api/smartthings.py:87-90)
RATE_LIMIT_DELAY = 0.5   # 每个请求间隔 0.5 秒
MAX_RETRIES = 3          # 最大重试 3 次
RETRY_DELAY = 1.0        # 重试间隔 1 秒
```

**工作流程**：
1. 缓存命中 → 直接返回，跳过限流
2. 缓存未命中 → 应用限流（`_rate_limit()`）→ 发起请求

---

## Q9: 生产环境有什么注意事项？

当前实现使用内存缓存，存在以下限制：

1. **进程重启丢失**：缓存存储在内存中，服务重启后缓存清空
2. **多实例不共享**：多实例部署时，各实例缓存独立
3. **无持久化**：无法保存到磁盘

**生产建议**：
- 考虑使用 Redis 替代内存缓存
- 添加缓存监控和统计
- 实现缓存预热机制

---

## Q10: 如何判断是否命中缓存？

通过日志可以观察缓存命中情况，当前使用 **INFO 级别**日志：

```
[Cache] HIT: key=GET:/devices/device-123        # 缓存命中
[Cache] MISS: key=GET:/devices/device-123       # 缓存未命中
[Cache] EXPIRED: key=GET:/devices/device-123    # 缓存已过期
[Cache] SET: key=GET:/devices/device-123, ttl=30s  # 缓存写入
[Cache] DELETE: key=GET:/devices/device-123     # 缓存删除
[Cache] CLEAR: cleared=5 entries                # 清空缓存
```

日志默认输出到标准输出，无需额外配置即可查看缓存状态。

---

## Q11: API 请求日志格式是怎样的？

SmartThings API 请求也带有详细的 INFO 级别日志：

```
[SmartThings API] REQUEST: method=GET, path=/devices/{id}, attempt=1/3
[SmartThings API] RESPONSE: method=GET, path=/devices/{id}, status=200
[SmartThings API] CLEAR_CACHE triggered
[SmartThings API] CLEAR_CACHE completed
```

这有助于追踪 API 调用链路和排查问题。
