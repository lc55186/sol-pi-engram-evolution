---
name: provider-config
description: 在 Hermes config
version: 1.0.0
category: imported
tags: []
metadata:
  hermes:
    tags: []
    source: IMA 知识库导入
---

# provider-config

> 在 Hermes config.yaml 中添加/修改 AI 提供商配置。 覆盖：新增 provider、设置主力模型、配置 fallback、更新 auxiliary models、 验证配置生效。适用于用户更换模型供应商、添加新 API Key、 调整 provider 优先级、配置多 provider 场景。 触发词：设置主力模型 / 添加 provider / 配置 API Key / 换模型 / fallback / 辅助模型 / 主力 / default model / provider 配置

# Provider Configuration — 提供商配置

## Procedure

### 1. 读取当前配置

```bash
hermes config show
```

确认当前 model.default、providers 中已有的 provider 列表、fallback\_providers。

### 2. 添加/修改 Provider

编辑 `~/.hermes/config.yaml` 的 `providers` 节：

```yaml
providers:
  <provider_name>:
    api_key: <key>
    base_url: <url>
    context_length: <int>
    models:
      - <model_name_1>
      - <model_name_2>
```

### 3. 设置主力模型

在 `model:` 顶层设置：

```yaml
model:
  provider: <provider_name>
  default: <model_name>
  base_url: <url>        # 也可在 provider 中定义
  api_key: <key>         # 敏感信息建议放 .env
  context_length: <int>
```

### 4. 配置 Fallback

在 `fallback_providers` 中按优先级排列：

```yaml
fallback_providers:
  - model: <primary_model>
    provider: <primary_provider>
  - model: <secondary_model>
    provider: <secondary_provider>
```

### 5. 批量切换 Provider（切换主力时必做）

切换到新 provider 时，必须将**所有** auxiliary 子模块一并切换，否则旧 provider 引用会导致 cron job 报错。

**方法 A：sed 批量替换**（推荐，快速）

```bash
cd ~/.hermes
# 1. 重命名 provider 定义节头（注意：必须单独处理，否则节头与实例不匹配）
sed -i 's/^  OLD_PROVIDER:/  NEW_PROVIDER:/' config.yaml

# 2. 批量替换 provider 实例、API Key、URL、model 名
sed -i \
  -e 's/provider: OLD_PROVIDER/provider: NEW_PROVIDER/g' \
  -e 's|api_key: OLD_KEY|api_key: NEW_KEY|g' \
  -e 's|base_url: OLD_URL|base_url: NEW_URL|g' \
  -e 's/model: OLD_MODEL/model: NEW_MODEL/g' \
  -e 's/default: OLD_MODEL/default: NEW_MODEL/g' \
  config.yaml

# 3. 替换 plugin 引用（image_gen/OLD_PROVIDER、video_gen/OLD_PROVIDER 等）
sed -i \
  -e 's|image_gen/OLD_PROVIDER|image_gen/NEW_PROVIDER|g' \
  -e 's|video_gen/OLD_PROVIDER|video_gen/NEW_PROVIDER|g' \
  config.yaml
```

**方法 B：Python 脚本**（精确，适合复杂条件）

```python
from hermes_tools import read_file, patch
import yaml
config = read_file("~/.hermes/config.yaml")
data = yaml.safe_load(config)
aux = data.get('auxiliary', {})
for name, cfg in aux.items():
    if cfg.get('provider') == 'OLD_PROVIDER':
        cfg['provider'] = 'NEW_PROVIDER'
        cfg['model'] = 'new-model'
with open('~/.hermes/config.yaml', 'w') as f:
    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
```

**方法 C：cronjob 工具逐个更新**（最可靠，但慢）

```
对每个 cron job 调用 cronjob(action='update', job_id='xxx', model={...})
```

### 6. 全量统一切换（用户要求"全部使用X模型"时）

当用户明确要求所有模型统一切换到某个 provider（如"所有辅助模型也全部使用Agnes"），必须执行两阶段切换：

**阶段一：Cron 任务**

* `cronjob(action='list')` 获取全部 job\_id
* 逐个调用 `cronjob(action='update', job_id=xxx, model={model: '新模型', provider: '新provider'})`
* 跳过 `no_agent=true` 的脚本型任务

**阶段二：Auxiliary 子模块**

* `python3 -c "import yaml; ..."` 读取 config.yaml 的 `auxiliary` 节
* 遍历所有子模块，筛选出 `provider != 目标provider` 或 `model != 目标模型` 的项
* 统一设置 `model`, `provider`, `api_key`, `base_url`
* 跳过专用模型（如 vision 的 agnes-image-2.1-flash）
* 写回 config.yaml

**验证：**

* 遍历所有 auxiliary 项确认无旧 provider 残留
* 确认专用模型（vision 等）未被误改

## Pitfalls

| **坑**                      | **症状**                                                                                                   | **Fix**                                                                                                                                                                                                    |                                                   |
| -------------------------- | -------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| **Gateway 内部无法重启**         | `hermes gateway restart` 报 "Blocked: cannot restart or stop the gateway from inside the gateway process" | 必须从外部 shell 执行，或等待下次会话自动加载                                                                                                                                                                                 |                                                   |
| **Auxiliary 残留旧 Provider** | 切换主力后 cron job 报 "Provider 'xxx' is set in config.yaml but no API key was found"                         | 批量替换所有 auxiliary 子模块的 provider（见步骤 5）                                                                                                                                                                      |                                                   |
| **NO\_PROXY 残留旧域名**        | 切换 provider 后旧域名仍在 NO\_PROXY 中，虽不影响功能但造成混乱                                                               | sed 清理 NO\_PROXY 中的旧域名（见步骤 6）                                                                                                                                                                              |                                                   |
| **代理连接重置**                 | 通过 socks5 代理访问国内 API 端点报 "connection reset"                                                              | 国内 API 用 `--noproxy '*'` 直连，不走代理                                                                                                                                                                           |                                                   |
| **API Key 远端拒绝**           | 格式/长度正确，但 `invalid_api_key` 或 "无效的令牌"                                                                    | 1. `echo -n "$KEY" \| xxd` 验长度无隐藏字符 2. `curl --noproxy '*'` 验 Bearer 格式 3. 用 `/models` 端点测试区分 key 问题 vs 模型问题。**注意**: 远端明确返回"无效的令牌"表示 key 格式被接受（HTTP JSON 错误响应），但密钥本身不在服务端有效密钥列表中 → **非网络/格式问题**，是账户/密钥状态问题 | 用户在控制台重新生成 key，不要反复试旧 key                         |
| **Key 重复确认**               | 用户说"给你的就是刚申请的"但实际发的 key 和 config.yaml 中已有 key 相同                                                         | 不要继续 test。立即 `grep api_key ~/.hermes/config.yaml` 对比 → 发现一致后报告"当前配置中就是这个 key，不是重复确认的问题，是远端拒绝了这个 key。请检查控制台账户状态、剩余额度，或生成新 key"                                                                              | 避免让用户反复确认同一个已配置的 key                              |
| **Key 轮换后 cron 仍报错**       | 新 key 已写入 config.yaml 但 cron 报 `API key not found`                                                       | `grep API_KEY ~/.bashrc` 检查环境变量                                                                                                                                                                            | 同步更新 `.bashrc` + `config.yaml` + `~/.hermes/.env` |
| **双 key 均被拒绝**             | 新旧两个 key 都返回 `invalid_api_key`                                                                           | 1. 确认 key 来源（同一控制台/不同账户）2. 检查账户状态（欠费/被封）3. 确认 API base\_url 正确                                                                                                                                             | 在控制台生成全新 key，不要复用旧 key 片段                         |
| **Anthropic 兼容端点**         | 提供商同时支持 OpenAI 和 Anthropic 两种协议时，需要配置两个 base\_url                                                        | OpenAI 兼容用 `/v1`，Anthropic 兼容用 `/anthropic`，在 auxiliary 中分别指定                                                                                                                                              |                                                   |
| **Provider 名冲突**           | 新 provider 名与已有 provider 重复                                                                              | 用 `hermes config show providers` 检查已有哪些 provider                                                                                                                                                           |                                                   |
| **Models 列表不完整**           | 新 model 不在 provider 的 models 列表中，WebUI 显示 "Unsupported model"                                            | 在 provider 的 models 数组中添加新 model 名                                                                                                                                                                         |                                                   |
| **API Key 泄露**             | 密钥明文写在 config.yaml                                                                                       | 敏感信息放 `~/.hermes/.env`，config 中用 `${VAR}` 引用                                                                                                                                                               |                                                   |
| **Plugin 引用遗漏**            | 切换后 WebUI 的图片/视频生成按钮报 "provider not found" 或空白                                                           | `image_gen/*` 和 `video_gen/*`                                                                                                                                                                              |                                                   |

## 触发条件

在 Hermes config.yaml 中添加/修改 AI 提供商配置。 覆盖：新增 provider、设置主力模型、配置 fallback、更新 auxiliary models、 验证配置生效。适用于用户更换模型供应商、添加新 API Key、 调整 provider 优先级、配置多 provider 场景。 触发词：设置主力模型 / 添加 provi
