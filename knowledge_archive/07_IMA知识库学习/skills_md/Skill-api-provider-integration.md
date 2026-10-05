# Skill-api-provider-integration

***

name: api-provider-integration
description: "第三方 AI API 提供商集成工作流：发现模型列表 → 连通性测试 → 配置验证 → 文档沉淀。当用户需要集成新的 AI API（如 SenseNova、Azure、本地模型服务）时激活。触发词：集成 API / 添加模型 / 测试 API / 配置 provider / 商汤日日新。"
tags: \["provider", "api", "integration"]
-----------------------------------------

# API Provider Integration — 第三方 AI API 集成

## Procedure

### 1. 发现可用模型

```bash
# OpenAI 兼容格式
curl -s -H "Authorization: Bearer $API_KEY" "$BASE_URL/models" | python3 -m json.tool

# 注意：部分 API 不返回完整模型列表，需查阅官方文档
```

### 2. 连通性测试

对每个候选模型执行：

```bash
# 基础聊天测试
curl -s -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MODEL_NAME",
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 50
  }' "$BASE_URL/chat/completions"

# 检查错误类型：
# - "model is not found" → 模型名错误
# - "quota exceeded" → 配额不足
# - "invalid_api_key" → Key 问题
# - 200 + reasoning 字段 → 需要关闭 reasoning 模式
```

### 3. 响应格式检查

**常见响应字段差异**:

* OpenAI 标准: `choices[0].message.content`
* SenseNova 默认: `choices[0].message.reasoning` (思维链模式)
* Anthropic: `content` 数组格式

**解决方案**:

```json
{
  "reasoning_effort": "none"
}
```

### 4. SDK 兼容性验证

```python
from openai import OpenAI

client = OpenAI(
    api_key="KEY",
    base_url="https://token.sensenova.cn/v1"  # 或自定义 URL
)

response = client.chat.completions.create(
    model="MODEL_NAME",
    messages=[{"role": "user", "content": "你好"}]
)
print(response.choices[0].message.content)
```

### 5. 配置写入

在 `~/.hermes/config.yaml` 中添加 provider：

```yaml
providers:
  <provider_name>:
    api_key: ${ENV_VAR_NAME}
    base_url: https://api.example.com/v1
    models:
      - model-name-1
      - model-name-2
```

### 6. 文档沉淀

将测试结果写入 `references/<provider-name>.md`：

* 可用模型列表
* 配置模板
* 使用注意事项
* 代码示例

***

## Pitfalls

| **坑**              | **症状**                                 | **Fix**                                                  |
| ------------------ | -------------------------------------- | -------------------------------------------------------- |
| **Reasoning 默认开启** | 响应返回 `reasoning` 字段而非 `content`        | 添加 `"reasoning_effort": "none"` 或读取 `reasoning` 字段       |
| **配额不足**           | `"Workspace allocated quota exceeded"` | 登录控制台充值或申请免费额度                                           |
| **模型名错误**          | `"model is not found"`                 | 查阅官方文档确认准确模型 ID                                          |
| **SDK 版本冲突**       | `extra_body` 参数报错                      | 升级 `openai` 包至最新版                                        |
| **Base URL 错误**    | 连接超时或 404                              | 确认 `/v1` 后缀是否需要                                          |
| **编码问题**           | GBK/UTF-8 混用导致乱码                       | 指定 `charset=utf-8` 或使用 `decode('gbk', errors='replace')` |

***

## Verification

1. `curl` 测试所有模型返回 200
2. Python SDK 调用成功
3. config.yaml 中添加 provider 无语法错误
4. 创建 `references/<provider>.md` 文档

***

## References

* `references/sensenova-api.md` — 商汤日日新 (SenseNova) API 模型列表、配置模板、使用注意事项
