# Skill-llm-wiki

***

name: llm-wiki
description: "Karpathy LLM-Wiki 知识库管理：增量构建持久化、结构化的 Markdown 知识库。 触发词：知识库 / 摄入知识 / 查知识 / 知识库健康检查 / knowledge base / 知识库维护 / 加入知识库。 适用：知识摄入（URL/文件→结构化摘要）、知识查询（问题→带来源的答案）、知识库维护（lint 检查）。 反例：不要触发于日常对话、代码开发、非知识管理类任务。"
version: 1.1.0
--------------

# LLM-Wiki 知识库管理

基于 Karpathy 的 LLM-Wiki 方法论，在 Hermes 内构建自动化知识管理系统。

## 架构

### 三层结构（Karpathy 原文）

```
~/.hermes/knowledge/
├── SCHEMA.md           ← 知识库 schema（结构+约定+工作流）
├── raw/                ← 原始来源（只读）
│   ├── articles/       ← 文章/博客
│   ├── papers/         ← 论文/文档
│   └── notes/          ← 笔记
├── wiki/               ← LLM 生成的结构化知识
│   ├── pages/          ← 来源摘要页
│   ├── entities/       ← 实体页面
│   ├── concepts/       ← 概念页面
│   ├── overview.md     ← 全局综述
│   ├── index.md        ← 目录索引
│   └── log.md          ← 操作日志
└── .git/               ← Git 版本控制
```

### 核心哲学

> "人类策展来源、提问、思考意义；LLM 干苦力——总结、交叉引用、归档、记账、维护。"

## 工作流

### 工作流 1：摄入（Ingest）

**触发：** "把 \[URL/文件] 加入知识库" / "摄入 \[主题]"

**Procedure：**

1. **获取内容**

```
# URL → web_extract
web_extract(urls=["https://example.com/article"])

# 文件 → read_file
read_file(path="/path/to/file.md")
```

2. **存入原始来源**

```bash
# 确定分类和文件名
# raw/articles/YYYY-MM-DD-{标题}.md
# raw/papers/YYYY-MM-DD-{标题}.md
# raw/notes/YYYY-MM-DD-{标题}.md
```

3. **运行摄入脚本**（辅助索引）

```bash
python3 ~/.hermes/scripts/knowledge-ingest.py raw/articles/2026-06-12-xxx.md --tag AI
```

脚本自动：提取标题/日期/标签/要点 → 更新 index.md → 追加 log.md → git commit

4. **读取 SCHEMA.md** 了解知识库结构
5. **生成 wiki 页面**（LLM 执行）
   * 摘要页 → `wiki/pages/YYYY-MM-DD-{slug}.md`
     * YAML frontmatter（title, type, created, updated, tags, sources, related）
     * 核心结论（一句话）
     * 关键要点（3-5 条）
     * 可执行步骤（如有）
   * 识别实体 → 更新/创建 `wiki/entities/{entity}.md`
   * 识别概念 → 更新/创建 `wiki/concepts/{concept}.md`
   * 在相关页面间添加双向链接
6. **更新索引和日志**
   * 更新 `wiki/index.md`（添加新条目）
   * 追加 `wiki/log.md`（记录摄入操作）
7. **Git commit**

```bash
cd ~/.hermes/knowledge
git add -A
git commit -m "feat: ingest {title}"
```

**Verification：**

* ✅ `wiki/pages/` 下有新页面
* ✅ `wiki/index.md` 包含新条目
* ✅ `wiki/log.md` 有新日志
* ✅ Git commit 成功

### 工作流 2：查询（Query）

**触发：** 用户提问（知识相关）

**Procedure：**

1. **运行查询脚本**（候选定位）

```bash
python3 ~/.hermes/scripts/knowledge-query.py "用户的查询" --top 5
```

脚本返回：相关页面路径 + 匹配摘要

2. **读取相关 wiki 页面**

```
read_file(path="~/.hermes/knowledge/wiki/pages/xxx.md")
read_file(path="~/.hermes/knowledge/wiki/concepts/xxx.md")
```

3. **综合回答**
   * 引用来源：`→ wiki/pages/xxx.md`
   * 如果 wiki 覆盖不足，用 web\_search 补充
4. **知识复利**（可选）
   * 好答案 → 存入 `wiki/pages/qa-{topic}.md`
   * 更新相关页面的关联链接

**Verification：**

* ✅ 回答包含知识库来源引用
* ✅ 如知识库覆盖不足，标注"知识库暂无，以下为搜索结果"

### 工作流 3：Lint（健康检查）

**触发：** "检查知识库" / "知识库健康状态" / cron 每周

**Procedure：**

1. **运行 lint 脚本**

```bash
python3 ~/.hermes/scripts/knowledge-lint.py --save
```

脚本检查：孤立页、过时页面、索引缺失、来源未覆盖、重复页面

2. **读取 lint 报告**

```
read_file(path="~/.hermes/knowledge/lint-reports/lint-{timestamp}.md")
```

3. **执行修复**（逐项）
   * 孤立页 → 添加关联链接或归档
   * 过时页面 → 更新内容
   * 索引缺失 → 更新 index.md
   * 来源未覆盖 → 生成 wiki 页面
   * 重复页面 → 合并
4. **Git commit**

```bash
git commit -m "fix: lint修复 {N} 个问题"
```

**Verification：**

* ✅ lint 报告生成
* ✅ 修复后重新 lint 问题数减少

## 脚本清单

> 详细用法见 [references/scripts-guide.md](references/scripts-guide.md)

| **脚本**                        | **功能**      | **用法**                                                             |
| ----------------------------- | ----------- | ------------------------------------------------------------------ |
| `scripts/knowledge-ingest.py` | 摄入来源 + 更新索引 | `python3 ~/.hermes/scripts/knowledge-ingest.py <path> [--tag tag]` |
| `scripts/knowledge-query.py`  | 查询知识库       | `python3 ~/.hermes/scripts/knowledge-query.py "query" [--top N]`   |
| `scripts/knowledge-lint.py`   | 健康检查        | `python3 ~/.hermes/scripts/knowledge-lint.py [--save]`             |

## 参考文档

* [Karpathy 原文架构](references/karpathy-architecture.md) — 三层结构、Schema、工作流、与传统 RAG 区别
* [脚本使用指南](references/scripts-guide.md) — 三个脚本的详细用法和典型工作流
* [实战部署笔记](references/deployment-notes.md) — 2026-06-13 搭建踩坑记录、集成点、关键决策

## 用户偏好

> 2026-06-13 用户明确要求：知识管理全自动，不需要手动触发。
>
> * 给 URL/文件 → 自动摄入
> * 提问 → 先查知识库，不足再搜 web
> * 有价值的搜索结果自动存入知识库（知识复利）
> * 与 agent-search、langfuse-alternative 自动链式调用

## 附录: SkillForge — 经验沉淀与技能复用

知识库不仅存储外部知识，还沉淀内部经验。SkillForge 是知识库的经验复用层。

### 核心流程

1. **沉淀**：任务完成后，耗时 >15min 或复杂度 >=3/5 → `skill_forge_engine.py extract`
2. **召回**：新任务开始前 → `skill_forge_engine.py auto "任务描述"` 检索已有经验
3. **共享**：所有 profile 共享 `~/.hermes/workspace/skill-forge/` 目录

### 技能模板格式

YAML frontmatter + Markdown body，包含 name/tags/trigger/applies\_to/success\_rate。详见 `references/skill-template-spec.md`。

### 与 LLM-Wiki 的关系

* **LLM-Wiki** = 外部知识摄入（URL/文章 → wiki 页面）
* **SkillForge** = 内部经验沉淀（任务 → 可复用技能模板）
* 两者互补：Wiki 存"别人知道什么"，Forge 存"我们经历过什么"

> 详见 `references/auto-tag-mapping.md`（自动标签映射表）

**核心规则（2026-06-13 用户明确要求）：所有知识库操作自动触发，不需要用户手动命令。**

* 用户给 URL/文件 → 自动摄入（web\_extract → knowledge-ingest.py → wiki 页面 → git commit）
* 用户提问 → 先查知识库（knowledge-query.py），不足再搜 web
* 知识库操作与 agent-search、langfuse-alternative 自动链式调用
* 新知识库工具安装 → 自动注册到 TOOLS-REGISTRY.md → 后续任务自动调用

## 附录: 项目调研与工具选型

研究外部 AI Agent 项目和工具，为知识库补充选型依据。

### 调研流程

1. **需求明确**：提取关键
