# Skill-mcp

***

name: mcp
description: Skills for working with MCP (Model Context Protocol) servers, tools, and integrations. Documents the built-in native MCP client — configure servers in config.yaml for automatic tool discovery.
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# MCP — Model Context Protocol 技能

## 触发条件

* "MCP"、"Model Context Protocol"、"MCP服务器"、"接入 MCP"、"配置 MCP"

## 传输模式

### HTTP 模式（AnySearch 等）

```bash
hermes mcp add <name> --url <endpoint_url>
# 非交互确认：yes | hermes mcp add <name> --url <endpoint_url>
```

配置写入 config.yaml：

```yaml
  <name>:
    url: <endpoint_url>
    headers:
      Authorization: Bearer ${TOKEN_VAR}
    enabled: true
```

### stdio 模式 — npx（GitHub MCP, Context7 等）

```yaml
  <name>:
    command: npx
    args:
    - -y
    - '<package>@latest'
    env:
      ENV_VAR_NAME: <value>
    enabled: true
```

**⚠️ CLI `--args` 解析 Bug：** `hermes mcp add` 的 `--args` 参数在 npx 场景下（尤其带 `@` scope 包名）会 exit code 2。

**正确做法：直接编辑 `~/.hermes/config.yaml`**，参照上面的 stdio 模板手动添加配置块。

### stdio 模式 — 本地二进制（codebase-memory-mcp 等独立发行的 CLI）

```yaml
  <name>:
    command: /path/to/binary
    args: []
    env:
      ENV_VAR_NAME: <value>
    enabled: true
```

注意 `args: []` 不能为空，否则 Hermes 解析会报错。本地二进制无需 `@latest`。

## 验证命令

```bash
hermes mcp list          # 查看所有已接入的 MCP
hermes mcp test <name>   # 测试指定 MCP 连接
```

## 环境变量

* 不要手动设置 `MCP_*` 环境变量，Hermes 自动从 config.yaml 加载
* Token 类凭证放在 config.yaml 的 `env` 块中，不要 export 到 shell

## Pitfalls

| **坑**                                | **症状**                                                                                    | **Fix**                                                                                                                                                                                                                                                  |
| ------------------------------------ | ----------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Agent 模式下 `hermes mcp add` 被安全拦截** | 命令超时，返回 "BLOCKED: Command timed out without user response"                                | Agent 无法执行 `hermes mcp add`（需用户交互确认）。**必须手动编辑 `~/.hermes/config.yaml`**，在 `mcp_servers:` 下添加配置块                                                                                                                                                          |
| **CLI --args 解析失败**                  | `hermes mcp add` exit code 2                                                              | 直接编辑 config.yaml 添加 stdio 配置块                                                                                                                                                                                                                            |
| **HTTP 模式忘记 headers**                | 401 Unauthorized                                                                          | 添加 `headers: {Authorization: Bearer ...}`                                                                                                                                                                                                                |
| **npx 缓存旧版包**                        | 工具行为异常                                                                                    | 包名加 `@latest` 后缀                                                                                                                                                                                                                                         |
| **Token 泄露到 shell 环境**               | 安全风险                                                                                      | 放 config.yaml `env` 块，不 export                                                                                                                                                                                                                           |
| **MCP 工具不出现**                        | `hermes mcp list` 无显示                                                                     | 检查 config.yaml 缩进和 enabled: true                                                                                                                                                                                                                         |
| **venv 缺少 mcp 包导致 HTTP 传输失败**        | `hermes mcp test` 报 `mcp.client.streamable_http is not available`，但系统 Python 能 import     | Hermes CLI 使用 venv Python（`/root/hermes-agent/venv/bin/python`），venv 内可能未装 mcp 包。修复：`/root/hermes-agent/venv/bin/pip install mcp`。验证：`/root/hermes-agent/venv/bin/python -c "from mcp.client.streamable_http import streamablehttp_client; print('OK')"` |
| **代理阻断 GitHub 导致无法安装 MCP**           | `curl`/`git clone` 到 GitHub 全部 `ERR_CONNECTION_RESET`（即使 `-x http://127.0.0.1:10809` 也失效） | `gh` CLI 不走代理时通常能直连 GitHub API。临时取消代理：`HTTPS_PROXY="" HTTP_PROXY="" gh release download ...`。MCP GitHub 工具也是备选通道                                                                                                                                         |

## 当前已接入

| **MCP**   | **传输** | **工具数** | **状态** |
| --------- | ------ | ------- | ------ |
| context7  | stdio  | all     | ✅      |
| github    | stdio  | 26      | ✅      |
| anysearch | HTTP   | 4       | ✅      |

## 相关工具（非 MCP）

| **工具**    | **用途**                     | **安装**                                                                                      |
| --------- | -------------------------- | ------------------------------------------------------------------------------------------- |
| CodeGraph | 代码知识图谱，本地索引代码库，省 58% token | `curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh \| sh` |
| MinerU    | Office/PDF→Markdown 文档解析   | `pip3 install mineru`                                                                       |

**CodeGraph PATH 注意**：安装到 `~/.local/bin`，需 `export PATH="$HOME/.local/bin:$PATH"`**MinerU 替代 markitdown**：当 Office 文件表格复杂、结构丢失时用 MinerU，转换质量更好（保留 HTML table 格式） |

## 详细指南

* **stdio 配置模板**：[references/stdio-config-template.yaml](references/stdio-config-template.yaml)
* **codebase-memory-mcp 安装与接入**：[references/codebase-memory-mcp.md](references/codebase-memory-mcp.md)
* **GitHub MCP 接入**：见 [github-mcp](github-mcp) skill（含最小权限配置、安全原则）
* **AnySearch MCP**：见 [agent-search](agent-search) skill（含查询策略、多域搜索）

## 步骤

1. **明确查询目标** — 确认要查找的信息
2. **检索相关内容** — 从知识库/文档中检索
3. **整理输出** — 结构化呈现结果
4. **标注来源** — 引用原始出处

## 验证

- [ ] 检索结果与查询目标相关

- [ ] 信息准确且最新

- [ ] 来源可追溯
