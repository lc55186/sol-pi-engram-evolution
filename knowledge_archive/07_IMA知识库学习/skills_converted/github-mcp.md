---
name: github-mcp
description: GitHub MCP 集成指南：用 Fine-Grained Token 接入，只读+提PR模式，最小权限原则
version: 1.0.0
category: devops
tags: ["github", "mcp", "git", "pr", "code-review"]
metadata:
  hermes:
    tags: ["github", "mcp", "git", "pr", "code-review"]
    source: IMA 知识库导入
---

# github-mcp

> GitHub MCP 集成指南：用 Fine-Grained Token 接入，只读+提PR模式，最小权限原则。 触发词：GitHub MCP / 接入 GitHub / 配置 GitHub Token / 操作 GitHub / git MCP。 适用：代码评审、PR 提交流程、仓库代码分析、Issue 管理。 反例：不要触发于简单 git 命令（用 terminal 即可）。

# GitHub MCP 集成指南

> **最小权限原则：** 只给需要的权限，不给 repo 级全权限。

## 接入步骤

### 0. 已知问题：CLI --args 解析失败

`hermes mcp add github --command npx --args "-y @modelcontextprotocol/server-github"` 在复杂 args 场景下 exit code 2。

**正确做法：直接编辑 config.yaml**，详见 [references/github-mcp-stdio-setup.md](./references/github-mcp-stdio-setup.md)

### 1. 创建 GitHub Personal Access Token

**方案 A：Classic PAT（推荐，简单）**

* 访问：[https://github.com/settings/tokens/new](https://github.com/settings/tokens/new)
* Token 名称：Hermes-MCP
* 过期时间：选 7-30 天
* **Scope**：勾选 `repo`（完整仓库访问）+ `read:org`
* Token 格式：`github_pat_...`

**方案 B：Fine-Grained Token（最小权限）**

* 访问：[https://github.com/settings/personal-access-tokens/new](https://github.com/settings/personal-access-tokens/new)
* Repository access：选 only select repositories
* Permissions：Contents: Read-only, Pull requests: Read & Write, Issues: Read & Write
* 限制：不支持搜索仓库、不支持 org 级操作

> 2026-06-13 实战：Classic PAT 成功接入，26 tools 全功能正常。Fine-Grained Token 限制较多，除非有明确安全需求，否则推荐 Classic PAT。

### 2. 接入 Hermes MCP

```bash
hermes mcp add github --command npx --args -y @modelcontextprotocol/server-github
# 当提示输入 Token 时，粘贴你刚才创建的 Fine-Grained Token
```

### 3. 验证接入

```bash
hermes mcp list  # 应显示 github 已启用
hermes mcp test github  # 应返回 Success
```

## 使用示例

```
"读 src/auth/ 下的逻辑，找那个硬编码超时，给修复方案，提 PR 别 merge，我审 diff。"
```

* Hermes 会：
  1. 读仓库代码（Contents: Read）
  2. 分析超时问题
  3. 生成修复方案
  4. 提 PR（Pull requests: Write）
  5. 不会 merge PR（Merge 权限没给）

## Pitfalls

| **坑**             | **症状**             | **Fix**                    |
| ----------------- | ------------------ | -------------------------- |
| **给全 repo 权限**    | 能修改整个仓库            | 选 only select repositories |
| **给 workflow 权限** | 能修改 GitHub Actions | 完全不选 workflow 权限           |
| **给 admin 权限**    | 能删除仓库/用户           | 完全不选 admin 权限              |
| **Token 过期**      | 401 错误             | 选足够长的过期时间，及时续签             |
| **repo 选错**       | 能访问不该访问的仓库         | 只勾选需要的仓库                   |

## Verification

接入后测试：

```bash
# 测试 GitHub MCP
hermes mcp test github

# 如果成功，查看可用工具
# GitHub MCP 提供以下工具：
# - search_repositories
# - get_file_contents
# - create_pull_request
# - list_pull_requests
# - get_issue
```

## 核心安全原则

> **"MCP 的诅咒是：接上太容易，收回太难。"**

1. 每次使用 GitHub MCP，只做需要的操作，做完后断开（用 hermes mcp remove github 移除，需要时再装）
2. Token 只存本地，不提交到代码
3. 不要永久 Token，选 7-30 天过期
4. 用 repo 级的最小权限，不是 org 级
5. 定期审查已接入的 MCP 服务器（每月一次）

## 步骤

1. **准备输入** — 确认输入数据和参数完整
2. **执行处理** — 调用工具完成核心逻辑
3. **输出结果** — 生成目标产物（文件/报告/状态）
4. **异常处理** — 失败时返回错误信息，不静默

## 验证

- [ ] 输出文件/报告已生成

- [ ] 处理逻辑覆盖主要场景

- [ ] 错误情况有明确提示

- [ ] 输出格式符合预期

## 触发条件

GitHub MCP 集成指南：用 Fine-Grained Token 接入，只读+提PR模式，最小权限原则。 触发词：GitHub MCP / 接入 GitHub / 配置 GitHub Token / 操作 GitHub / git MCP。 适用：代码评审、PR 提交流程、仓库代码分析、Issue 管理。 反例：不要触发于简单 git 命令（用 te
