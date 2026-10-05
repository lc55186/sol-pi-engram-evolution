# Skill-index-browser-agent

***

name: index-browser-agent
description: >
Index — Laminar AI 团队的浏览器 Agent 框架。基于 Playwright + LLM 视觉推理，
自动执行复杂网页任务。支持结构化输出、本地 Chrome、会话持久、可视化追踪。
触发词：Index / lmnr-index / 浏览器Agent / 自动化浏览器 / 网页抓取 / 结构提取。
version: 2.0.0
author: Hermes
license: MIT
platforms: \[linux, macos, win]
tags: \[index, browser-agent, playwright, llm, automation, scraping, lmnr]
metadata:
hermes:
tags: \[index, browser-agent, playwright, llm, automation, scraping, lmnr]
category: automation
related\_skills: \[browser-automation, kitesurf-browser, kitesurf-research]
requires\_toolsets: \[terminal, file, web]
------------------------------------------

# Index Browser Agent — Laminar AI 浏览器 Agent

## When to Use

* 用户询问 Laminar AI 团队的 Index 项目
* 需要**浏览器 Agent 执行复杂网页任务**（点击、填表、导航）
* 需要**结构化输出**（JSON/Pydantic schema）
* 需要**本地 Chrome 复用登录态**
* 需要**可视化追踪**（Agent 操作录屏+Trace）

**不适用**：大规模并发（用 Kitesurf）、视频/WebGL、实时交互（延迟较高）。

## 项目信息

| **项目**     | **详情**                                                               |
| ---------- | -------------------------------------------------------------------- |
| **GitHub** | [https://github.com/lmnr-ai/index](https://github.com/lmnr-ai/index) |
| **PyPI**   | `lmnr-index` (v0.1.13)                                               |
| **团队**     | Laminar (YC S24)                                                     |
| **创始人**    | Robert Kim (skull8888888)                                            |
| **许可证**    | MIT                                                                  |
| **Python** | >= 3.10                                                              |

## 核心定位

Index 是**浏览器 Agent 框架**（控制真实浏览器），不是浏览器引擎：

* 基于 Playwright + LLM 视觉推理
* 支持结构化输出（Pydantic schema）
* 可复用本地 Chrome 登录态
* 完整操作录屏追踪

## 快速上手

### 1. 安装

```bash
pip install lmnr-index 'lmnr[all]'
playwright install chromium
```

### 2. 配置模型 Key

```bash
# .env 或 export
export GEMINI_API_KEY=xxx
export ANTHROPIC_API_KEY=xxx
export OPENAI_API_KEY=xxx
export LMNR_PROJECT_API_KEY=xxx  # 可选，用于追踪
```

### 3. CLI 交互模式

```bash
index run
# 选择模型 → 输入任务 → Agent 自动执行

# 使用本地 Chrome（复用登录态）
index run --local-chrome
```

### 4. Python API

```python
import asyncio
from index import Agent, GeminiProvider
from pydantic import BaseModel

class NewsSummary(BaseModel):
    title: str
    summary: str

async def main():
    llm = GeminiProvider(model="gemini-2.5-pro-preview-05-06")
    agent = Agent(llm=llm)
    output = await agent.run(
        prompt="Navigate to news.ycombinator.com, find a post about AI, extract title and summary",
        output_model=NewsSummary
    )
    print(output.result.content)

asyncio.run(main())
```

### 5. CLI 工具

```bash
# 导航+提取
python3 ~/.hermes/skills/index-browser-agent/scripts/index_tool.py run "打开 example.com 提取标题"

# 结构化输出
python3 ~/.hermes/skills/index-browser-agent/scripts/index_tool.py extract "抓取 HN 前3条新闻" --schema hn_news

# 本地 Chrome 模式
python3 ~/.hermes/skills/index-browser-agent/scripts/index_tool.py run "查看 GitHub 通知" --local-chrome
```

### 6. Serverless API 模式

```python
from lmnr import Laminar, LaminarClient

Laminar.initialize(project_api_key="your_key")
client = LaminarClient(project_api_key="your_key")

for chunk in client.agent.run(
    stream=True,
    model_provider="gemini",
    model="gemini-2.5-pro-preview-05-06",
    prompt="Navigate to news.ycombinator.com, find a post about AI, and summarize it"
):
    print(chunk)
```

## 支持模型

| **模型**            | **特点**                  |
| ----------------- | ----------------------- |
| Gemini 2.5 Pro    | 快速准确（推荐）                |
| Claude 3.7 Sonnet | 可靠准确（extended thinking） |
| OpenAI o4-mini    | 速度/成本/准确率平衡             |
| Gemini 2.5 Flash  | 极快低成本                   |

## 性能对比

| **维度** | **Index** | **Playwright 原生** | **Kitesurf** |
| ------ | --------- | ----------------- | ------------ |
| 交互能力   | ⭐⭐⭐⭐⭐     | ⭐⭐⭐⭐              | ⭐            |
| 结构化输出  | ⭐⭐⭐⭐⭐     | ⭐⭐                | ⭐            |
| 并发能力   | ⭐⭐⭐       | ⭐⭐⭐⭐              | ⭐⭐⭐⭐⭐        |
| 成本     | ⭐⭐⭐       | ⭐⭐⭐⭐⭐             | ⭐⭐⭐⭐⭐        |
| 追踪调试   | ⭐⭐⭐⭐⭐     | ⭐⭐                | ⭐⭐           |

## 架构

```
┌─────────────────────────────────────────────────────┐
│                  Index Agent Layer                   │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐ │
│  │   LLM       │  │  Vision     │  │  Pydantic    │ │
│  │  Provider   │  │  Reasoning  │  │  Output      │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘ │
└─────────┼────────────────┼────────────────┼──────────┘
          │                │                │
┌─────────▼────────────────▼────────────────▼──────────┐
│              Playwright Browser Control              │
│  ┌──────────────────────────────────────────────────┐ │
│  │  • Navigation                                    │ │
│  │  • DOM Interaction                               │ │
│  │  • Screenshot capture                            │ │
│  │  • Cookie/Session management                     │ │
│  └──────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

## 与竞品对比

| **特性**    | **Index** | **Kitesurf** | **BrowserUse** | **Agent-E** |
| --------- | --------- | ------------ | -------------- | ----------- |
| 本地 Chrome | ✅         | ❌            | ✅              | ✅           |
| 结构化输出     | ✅         | ❌            | ❌              | ✅           |
| 会话持久      | ✅         | ❌            | ✅              | ✅           |
| 云端部署      | ❌         | ✅            | ❌              | ❌           |
| 录屏追踪      | ✅         | ❌            | ❌              | ✅           |
| 成本        | API 费用    | Beta 免费      | 自建             | API 费用      |
| 复杂任务      | ⭐⭐⭐⭐⭐     | ⭐⭐           | ⭐⭐⭐⭐           | ⭐⭐⭐⭐        |
| 大规模并发     | ⭐⭐        | ⭐⭐⭐⭐⭐        | ⭐⭐             | ⭐⭐          |

## References

* `references/research-notes-2026-08-09.md` — 研究笔记
* `references/patterns.md` — 使用模式与最佳实践
* `references/troubleshooting.md` — 常见问题

## Pitfalls

### 1. 需要 API Key

**问题**：未设置 GEMINI\_API\_KEY / ANTHROPIC\_API\_KEY / OPENAI\_API\_KEY

**解决**：至少配置一个模型 Key

### 2. playwright install 必须手动执行

**问题**：安装 lmnr-index 后无法启动浏览器

**解决**：运行 \`play
