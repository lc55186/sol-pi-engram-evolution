# WeKnora 研究报告 — BOSS-AI-R 可复用技术清单

> 研究日期：2026-09-18
> 来源：https://github.com/Tencent/WeKnora

---

## 1. 项目概况

| 维度 | 内容 |
|------|------|
| **名称** | WeKnora（维娜拉） |
| **厂商** | 腾讯（Tencent） |
| **定位** | 开源 LLM 知识管理平台：文档 → RAG + Agent + 自维护 Wiki |
| **Stars** | 26.4k |
| **Forks** | 3.6k |
| **版本** | v0.8.0 |
| **协议** | MIT |
| **技术栈** | Go + Vue 3 + PostgreSQL/SQLite + Docker |
| **核心能力** | RAG 问答 + ReACT Agent + 自维护 Wiki + MCP Server |

---

## 2. 可复用模块清单

### 2.1 MCP Server（29 个工具）

| 项 | 内容 |
|------|------|
| **语言** | Go |
| **传输** | stdio / SSE / HTTP |
| **工具数** | 29 个（4 组） |
| **复用方式** | 直接作为 BOSS-AI-R 的知识库 MCP 服务器 |

**工具分组：**
| 分组 | 工具数 | 功能 |
|------|--------|------|
| 检索与读取 | ~10 | 知识库查询、文档读取 |
| Agent 调用 | ~5 | 同步问答、会话管理 |
| Wiki 工具 | ~8 | 搜索/读取/索引 Wiki |
| 写入工具 | ~6 | 文档新增/更新/删除 |

**快速集成：**
```bash
pip install tencent-weknora-mcp
# 或
npx @modelcontextprotocol/server-weknora
```

### 2.2 DocReader 文档解析引擎

| 项 | 内容 |
|------|------|
| **语言** | Go + gRPC |
| **端口** | 50051 |
| **支持格式** | PDF/Word/Txt/Markdown/HTML/EPUB/MHTML/图片/CSV/Excel/PPT/JSON/XMind |
| **核心能力** | OCR、表格识别、版面分析、VLM 多模态解析 |
| **复用方式** | 作为合同/报价单解析后端服务 |

**可复用的分块策略：**
- 自适应三层分块（段落 → 章节 → 文档）
- 父子分块（Parent-Child Chunking）
- 按批次解析配置（`process_config`）

### 2.3 混合检索引擎

| 项 | 内容 |
|------|------|
| **策略** | BM25 + Dense + GraphRAG + 父子分块 |
| **向量库** | pgvector HNSW（1024维）、Milvus、Qdrant、Weaviate |
| **重排** | 火山引擎 Rerank、腾讯云 LKEAP、智谱 AI |
| **复用方式** | 替换/增强当前 `graph_retriever.py` |

**检索策略对比：**
| 策略 | WeKnora | 我们当前 | 差距 |
|------|---------|---------|------|
| BM25 稀疏召回 | ✅ | ❌ | 需新增 |
| Dense 稠密召回 | ✅ | ⚠️ 基础 | 需增强 |
| GraphRAG 图谱增强 | ✅ | ✅ Engram | 已对齐 |
| 父子分块 | ✅ | ❌ | 需新增 |
| RRF 融合排序 | ✅ | ❌ | 需新增 |
| 多向量库扇出 | ✅ | ❌ | 可选 |

### 2.4 ReACT Agent 模式

| 项 | 内容 |
|------|------|
| **模式** | ReACT（Reasoning + Acting） |
| **能力** | 自主编排知识检索、MCP 工具、技能沙箱、网络搜索 |
| **复用方式** | 参考其 Agent 编排逻辑，增强 `pipeline.py` |

**Agent 编排流程：**
```
用户提问 → 意图分析 → 工具选择（知识库/MCP/搜索）
    → 执行工具 → 结果评估 → 生成回答 → 引用溯源
```

### 2.5 Wiki 模式

| 项 | 内容 |
|------|------|
| **功能** | 从原始文档自治生成结构化 Markdown Wiki + 知识图谱 |
| **特性** | 页面版本历史、行级 diff、一键回滚、可视化知识图谱 |
| **复用方式** | 可用于谈判案例库自动生成 |

### 2.6 技能沙箱运行时

| 项 | 内容 |
|------|------|
| **后端** | Docker / E2B / Cube 沙箱 |
| **网络** | 按空间配置网络策略 |
| **能力** | shell_exec、文件工具、产物收集 |
| **复用方式** | BOSS-AI-R 的合规沙盒隔离层可参考 |

### 2.7 数据源导入

| 项 | 内容 |
|------|------|
| **支持源** | 飞书知识库/云盘、Lark、GitLab、腾讯 IMA、Notion、语雀、钉钉文档、RSS |
| **复用方式** | 未来对接老板企业的知识源 |

### 2.8 长期记忆系统

| 项 | 内容 |
|------|------|
| **分类** | profile / preference / fact / task / interest |
| **能力** | 自动抽取、用户确认、按需 search_memory |
| **复用方式** | 替代 OpenHuman Memory Tree 方案，作为 BOSS-AI-R 长期记忆 |

---

## 3. 集成优先级建议

| 优先级 | 模块 | 接入方式 | 预估工作量 |
|--------|------|---------|----------|
| P0 | MCP Server | pip install 直接使用 | 1-2 天 |
| P0 | 混合检索策略 | 复用 BM25 + 父子分块 + RRF | 3-5 天 |
| P1 | DocReader 分块 | 复用自适应三层分块逻辑 | 2-3 天 |
| P1 | ReACT Agent 编排 | 参考其工具选择 + 引用溯源 | 5-7 天 |
| P2 | Wiki 模式 | 谈判案例库自动生成 | 7-10 天 |
| P2 | 技能沙箱运行时 | 合规沙盒隔离层 | 5-7 天 |
| P3 | 长期记忆系统 | 跨会话记忆管理 | 3-5 天 |

---

## 4. 与 BOSS-AI-R 当前架构映射

| WeKnora 模块 | BOSS-AI-R 对应 | 集成方式 |
|-------------|---------------|---------|
| MCP Server | 新增模块 | 作为知识库查询接口 |
| DocReader | format_converter.py | 复用解析策略 |
| 混合检索 | graph_retriever.py | 增强现有检索 |
| ReACT Agent | pipeline.py | 参考编排逻辑 |
| Wiki 模式 | 新增模块 | 案例库自动生成 |
| 长期记忆 | observation_pack.py | 替代 TokenJuice 方案 |

---

## 5. 参考资源

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/Tencent/WeKnora |
| 中文 README | https://github.com/Tencent/WeKnora/blob/main/README_CN.md |
| MCP 配置 | https://github.com/Tencent/WeKnora/blob/main/mcp-server/MCP_CONFIG.md |
| DocReader 文档 | https://github.com/Tencent/WeKnora/tree/main/docreader |
| 产品官网 | https://weknora.weixin.qq.com/ |

---

*V1.0 | 2026-09-18*
