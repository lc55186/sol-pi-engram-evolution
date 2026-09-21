# GitHub 4个AI开源神项 — 补充分析

> 来源：2026-09 头条文章，已归档至 `knowledge_archive/06_开源项目研究/`

## 文章介绍的4个项目

| # | 项目 | 定位 | 核心机制 |
|---|------|------|---------|
| 1 | **Superpowers** (obra/superpowers) | 给编程AI装"资深架构师大脑" | 设计文档→任务拆解→TDD/DRY 强制执行 |
| 2 | **Deep-Live-Cam** (hacksider) | 实时换脸GUI工具 | 摄像头/视频一键换脸，伦理标注要求 |
| 3 | **OpenCode** (anomalyco/opencode) | 开源终端编程 Agent | **Plan 模式（只读分析）→ Build 模式（动手写码）分离** |
| 4 | **Dexter** (virattt/dexter) | 金融研究 AI Agent | 研究计划→市场数据→自我校验→**Loop Detection 防钻牛角尖** |

## 与之前研究的对比

这篇是**不同的4个项目**（早期文章），与 Ponytail/Caveman 系列互补：

| 维度 | 早期4项（本篇） | 后期TOP项目（之前研究） |
|------|----------------|----------------------|
| 代码质量 | Superpowers（TDD纪律） | Ponytail（懒专家，-54%代码） |
| 试错控制 | **OpenCode（Plan/Build分离）** | Caveman（Token压缩65%） |
| 防失控 | **Dexter（Loop Detection）** | Headroom（输出压缩） |
| 任务拆解 | Superpowers（小任务拆解） | agent-skills（工程技能库） |

## 对 BOSS-AI-R 的额外启发

### 1. Plan/Build 模式分离（OpenCode）→ 可直接落地
- **当前问题**：我改代码偶尔也会"上来就改"
- **改进**：复杂变更前先输出只读分析（Plan），确认方案后再动手（Build）
- 已在 `systematic-debugging` 技能中有类似思路，但可强化为显式两步

### 2. Loop Detection（Dexter）→ 补入预警机制
- **金融场景**：AI 反复尝试同一错误路径时自动中断
- **谈判场景映射**：如果 ASR→意图分析连续 N 轮失败，自动降级为纯关键词模式
- 这比"继续猜"更可靠——与"失败→阻塞等待"原则一致

### 3. TDD 强制（Superpowers）→ 已部分落地
- 当前 302 测试全绿，但新功能有时先写代码后补测试
- 强化：核心模块变更先写/改测试，再改实现

## 结论

这4个项目的**核心共性**与之前研究一致：AI Agent 的价值不是"生成更多"，而是"有纪律地工作"——先想清楚（Plan）、拆小任务（Decompose）、卡住就停（Loop Detection）、验证再交付（TDD）。

这些原则已通过 self-evolution + systematic-debugging + github-ai-projects-2026 三个技能固化到工作流中。
