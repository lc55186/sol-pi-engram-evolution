# Skill-self-evolution

***

name: self-evolution
description: "Self-Evolution 进化体系总览：整合 darwin-skill（9维rubric优化）、adversarial-evaluator（对抗式评估）、skill\_utility\_tracker（效用追踪）、self-harness（自进化门控）四大子系统。当需要了解整体进化架构、选择进化工具、或协调多个子系统时使用。"
version: 2.1.0
author: Hermes Agent
license: MIT
metadata:
hermes:
tags: \[self-evolution, optimization, skill-quality, darwin, adversarial]
related\_skills: \[darwin-skill, adversarial-evaluator, gstack, mindforge-skill, self-evolving-agent, learning-engine, self-harness]
------------------------------------------------------------------------------------------------------------------------------------

# Self-Evolution 进化体系 v2.0

> 本技能是进化体系的**总览入口**，不替代具体子系统的 SKILL.md。
> 详细操作见各子系统技能文件。

## 体系架构

```
Self-Evolution v2.0
├── darwin-skill              # Skill 质量评估 + 自主优化循环
├── adversarial-evaluator     # 任务产出质量对抗式评估
├── skill_utility_tracker     # Skill 效用 EMA 追踪 + 衰减
├── smart_router              # 子 Agent 级模型路由（省成本）
├── memory_inspector          # 记忆白盒化管理
├── dream_mode                # 记忆压缩 + 回滚点
├── always_on                 # 后台系统监控
├── surrogate_verifier        # 共进化验证器（P1 子系统）
├── mindforge-skill           # 思维熔炉：逆向工程→人物/主题Skill蒸馏（nuwa-skill优化版）
├── self-evolving-agent       # 自进化Agent框架：9原子工具+5层记忆+技能结晶化（GenericAgent优化版）
├── learning-engine           # 自动化学习引擎：7步学习闭环（SOUL→规划→拆解→测试→应用→进化→循环）
├── skill-forge              # 跨Agent技能复用：经验沉淀+技能召回（Multica灵感，轻量实现）
├── skillopt-integrator     # SkillOpt文本空间训练：ReflACT循环（微软，arXiv 2605.23904）
├── skillopt-sleep          # SkillOpt夜间巩固插件（微软官方）
└── self-harness             # 自进化门控：失败收集→缺陷分类→回归测试→周度报告
```

## 三个进化层次

| **层次**          | **工具**                  | **触发方式**       | **作用对象**              |
| --------------- | ----------------------- | -------------- | --------------------- |
| **Skill 质量**    | darwin-skill            | 手动/定期 cron     | SKILL.md 本身           |
| **任务产出**        | adversarial-evaluator   | 每次主观任务         | Generator 的输出         |
| **Skill 效用**    | skill\_utility\_tracker | 每次 Skill 使用后自动 | Skill 的 EMA 分数        |
| **Harness 自进化** | self-harness            | 失败驱动 + 周度定时    | SOUL.md / Skill / 提示词 |

## 子系统选择指南

**想优化 Skill 本身的质量？** → `darwin-skill`

* 9 维 rubric 评分 + hill-climbing 优化 + git 版本控制
* 用于：新 Skill 创建后评审、现有 Skill 定期体检

**想评估一次任务的产出质量？** → `adversarial-evaluator`

* Generator-Evaluator 分离 + 独立上下文 + 结构化评分
* 用于：设计/文案/方案等主观任务的产出把关

**想蒸馏一个人物/主题的思维框架为可运行 Skill？** → `mindforge-skill`

* 多源信息采集（并行 Agent Swarm）+ 思维框架提炼 + 三层质量验证
* 用于：创建人物 Skill、主题方法论 Skill、思维顾问

**想让 Agent 自主探索新能力、自动积累技能？** → `self-evolving-agent`

* 9 原子工具 + 5 层记忆 + 技能结晶化协议 + 进化审计链
* 用于：构建自进化 Agent、自动技能生长、子 Agent 编排

**想让 Hermes 学习新知识、自动沉淀为永久资产？** → `learning-engine`

* 7 步学习闭环（SOUL 初始化→路径规划→深度拆解→测试回忆→应用转化→自我进化→循环）
* 支持多主题并行执行（实战验证：4主题×6模块×30天 并行启动，\~15分钟生成20个文件）
* 用于：学习任何新主题、自动创建 Skill 文档、永续知识积累、批量技能生成

**想让不同 Agent/Profile 共享经验、避免重复踩坑？** → `skill-forge`

* 经验沉淀（extract）+ 技能召回（recall/auto）+ 跨 Profile 共享
* 用于：多 Agent 协作、技能库积累、经验复用

**想在文本空间迭代优化 Skill 文档本身？** → `skillopt-integrator`

* 微软开源 (arXiv 2605.23904, 5k+⭐)，把 Skill 文档当可训练权重，ReflACT 六阶段循环
* Rollout(前向传播) → Reflect(分析失败) → Aggregate(合并) → Select(裁剪) → Update(应用) → Validate(门控)
* 零推理开销、跨模型复用、MIT 协议
* 用于：Skill 连续不达标时自动训练、夜间巩固、周度进化

**想让 Agent 从执行失败中自我优化 Harness？** → `self-harness`

* 失败案例收集 → 18类缺陷分类 → 回归测试门控 → 周度进化报告
* 用于：分析执行失败模式、修复 Harness 缺陷、建立回归测试、运行 Self-Harness 进化循环

**安全审计 MCP Server 配置？** → 参考外部知识库 `references/external-mcp-security-2026.md`

* 8 大攻击向量 + 5 层防御框架 + 行动项清单
* 用于：MCP Server 安全加固、权限审计、配置审查

## NVIDIA RQGM 论文 · 评估器共进化（2026-06-29 更新）

> arXiv:2606.26294 · 剑桥 + NVIDIA · 红皇后哥德尔机（Red Queen Gödel Machine）
> 完整分析见 `references/rqgm-evaluator-coevolution.md`

### 核心概念

* **哥德尔机**（2003 Schmidhuber）：数学证明门槛无限大，20年未实现
* **RQGM 突破**：绕过数学证明，用**进化+筛选**替代
* **受控效用进化**：epoch 冻结 → 基准真相锚定 → 选择性擦除
* **2028 预测修正**：SRSI 60%、URSI ≤10%、ASI ≤5%

### 可移植到 Hermes 的 3 个机制

1. **影子评估器** — 每次 SOUL.md 变更后跑回归（见 `references/shadow-evaluator-design.md`、`scripts/shadow-evaluator.py`）
2. **评估共进化沙盒** — 未来可隔离测试行为变化
3. **2028 RSI 预测框架** — `references/rsi-prediction-framework-2026.md`

## 外部知识库索引

| **知识库**                    | **来源**                       | **位置**                                               | **状态** |
| -------------------------- | ---------------------------- | ---------------------------------------------------- | ------ |
| MCP Security 2026          | aibuzz.blog + nimblebrain.ai | `references/external-mcp-security-2026.md`           | ✅ 已引入  |
| Agent Memory 分层架构          | analyticsvidhya.com 2026.04  | —                                                    | 📋 待整理 |
| Skill 最佳实践                 | agentskills.io + mgechev     | 内联到 Skill 质量门禁                                       | ✅ 已引入  |
| Agent 自进化生态全景              | 6大开源项目深度对比 (2026-06-07)      | `references/2026-06-07-agent-evolution-landscape.md` | ✅ 已引入  |
| SkillForge 技能复用系统          | Multica 灵感，轻量实现 (2026-06-07) | 外部 Skill: `skill-forge`                              | ✅ 已引入  |
| GitHub Trending 2026-06-10 | GitHub Trending + 人工评估       | `references/2026-06-10-github-trending-analysis.md`  | ✅ 已引入  |

## 当前进化状态

| **Skill**             | **darwin 评分** | **最近使用**   | **EMA** | **下次审查**   |
| --------------------- | ------------- | ---------- | ------- | ---------- |
| adversarial-evaluator | 67.6          | 2026-05-31 | 0.574   | 2026-06-30 |
| self-harness          | —             | 2026-07-23 | —       | 2026-07-30 |

### 2026-07-23 周度审计关键发现

**技能健康度**：

* 171 个 SKILL.md，105 个被 Curator 追踪
* 36 个活跃（34.3%），69 个零使用（65.7%）
* 5 个技能缺少 description（firecrawl, java-core, python-core, ima-skill/knowledge-base, ima-skill/notes）
* Archive 区 19 个过期技能占 1.4MB，需清理

**冗余识别**：

* IMA 知识库：`ima`(use=27) vs `ima-skill`(use=10) — 建议统一入口
* 自进化体系：`continuous-learning`(use=2)、`auto-hermes`(use=1) 可合并入 `self-evolution`
* 运维诊断：`deployment-troubleshooting`(use=5) 应并入 `sysops-toolkit`

\*\*Cron 膨胀
