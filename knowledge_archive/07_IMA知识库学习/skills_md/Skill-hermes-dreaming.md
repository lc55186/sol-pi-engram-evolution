# Skill-hermes-dreaming

***

name: hermes-dreaming
description: Hermes 梦境系统（Dreaming Engine）。模拟生物睡眠记忆巩固，跨会话自动提取偏好/项目/技能洞察并写入记忆。三维度梦境：偏好梦境（用户偏好提取）、项目梦境（架构决策/里程碑/故障模式）、技能梦境（工具使用/效率瓶颈/新技能候选）。支持定时自动运行、手动触发、dry-run 分析、梦境报告生成。当用户说"启动梦境"、"记忆巩固"、"让 Hermes 做梦"、"梦境整理"时激活。
version: 2.4.0
--------------

# Hermes Dreaming System — 梦境系统

## 触发条件

* 用户说"启动梦境"、"记忆巩固"、"让 Hermes 做梦"、"梦境整理"
* 定时自动运行（默认每天 23:10，在记忆分页维护后 5 分钟）
* 记忆系统健康检查发现信噪比下降时建议触发

## 核心架构

### 类比生物睡眠

| **睡眠阶段**  | **Hermes 对应** | **功能**       |
| --------- | ------------- | ------------ |
| 慢波睡眠（SWS） | 偏好梦境 + 项目梦境   | 模式提取、记忆合并、去重 |
| 快速眼动（REM） | 技能梦境 + 跨领域关联  | 创意洞察、新连接发现   |
| 觉醒期       | 记忆写入 + 报告生成   | 写入归档、输出报告    |

### 三维度梦境

#### 1. 偏好梦境（Preference Dream）

扫描会话记录，提取：

* 回复风格偏好（简洁/详细/中文）
* 工作风格偏好（自主决策/先验证/系统性）
* 技术偏好（语言/框架/工具链）
* 沟通偏好（结论先行/不要客套）
* 投资偏好（短线/波段/技术分析）
* 矛盾检测（频繁修正 = 之前行为不符预期）
* 时间感知（即将到期 → 已过期 自动更新）

#### 2. 项目梦境（Project Dream）

扫描会话记录，提取：

* 架构决策（选型理由、方案确定）
* 技术模式（最佳实践、设计范式）
* 项目里程碑（完成/进行中/下一步）
* 故障/问题（根因分析、修复方案）
* 代码质量（重构/测试/优化）
* 跨项目模式（共同技术栈、通用解决方案）

#### 3. 技能梦境（Skill Dream）

扫描会话记录，提取：

* 工具使用频率（哪些工具最常用）
* 工作流模式（操作序列、步骤顺序）
* 效率瓶颈（超时/失败/重复操作）
* 成功模式（高效/一次成功）
* 潜在新技能候选（重复操作序列可封装）

## 使用方式

### Dream Keeper v2（生产环境默认，2026-07-20 起）

> **架构变更**：从"Agent 手动梦境"升级为"Python handler + Cron 双触发"。handler.py 负责结构化处理，Cron 负责调度。Agent 只做报告解读。

#### 手动运行

```bash
# 完整梦境（含空闲检测）
python3 /root/.hermes/plugins/dream-keeper/handler.py --auto

# 仅分析，不写入日志
python3 /root/.hermes/plugins/dream-keeper/handler.py --dry-run

# 指定维度
python3 /root/.hermes/plugins/dream-keeper/handler.py --dimension preference
python3 /root/.hermes/plugins/dream-keeper/handler.py --dimension project
python3 /root/.hermes/plugins/dream-keeper/handler.py --dimension skill

# 查看状态
cat /root/.hermes/dream_state.json
```

#### 状态字段

| **状态**                 | **含义**     | **何时出现**                 |
| ---------------------- | ---------- | ------------------------ |
| `dreamed`              | 成功写入梦境日志   | CPU 空闲 >85% 且 handler 完成 |
| `skipped_not_idle`     | CPU 不空闲，跳过 | 系统繁忙                     |
| `skipped_no_sessions`  | 无新会话可分析    | 近期无活跃会话                  |
| `skipped_tool_blocked` | 工具不可用      | FTS5 等被禁                 |

#### 产出文件

* **结构化日志**：`/root/.hermes/logs/dreaming/dream_YYYYMMDD_HHMMSS.json`
  * 字段：`reason`, `type`, `improvement`, `insights[]`, `vaccines[]`, `skill_candidates[]`
* **状态跟踪**：`/root/.hermes/dream_state.json`

#### 定时任务

| **Cron**            | **频率**   | **作用**                            |
| ------------------- | -------- | --------------------------------- |
| `dream-keeper-idle` | 每 30 分钟  | CPU 空闲 >85% 时触发 handler.py --auto |
| `梦境巩固+记忆维护`         | 每日 23:10 | 完整三维度反思 + 记忆维护（Agent 执行）          |

### Agent-Driven Consolidation（23:10 定时任务使用）

当 Cron 触发每日 23:10 梦境巩固时，由 Agent 直接执行以下工作流：

1. **搜索最近 24h 会话**

```
session_search(query="*", sort="newest", limit=10)
```

2. **读取当前 MEMORY.md 状态**

```
read_file("~/.hermes/MEMORY.md")
read_file("/root/MEMORY.md")
```

3. **三维度提取洞察** → 偏好/项目/技能
4. **去重判断** — 对比 L1 索引，只保留真正新的洞察
5. **更新 L1 索引** — `patch` 编辑，不用 `memory` 工具
6. **输出报告** — 有洞察则报告，无新洞察则 `[SILENT]`

#### 关键判断规则

* **新洞察标准**: 此前 MEMORY.md 中完全不存在的内容，或状态发生实质性变化
* **去重标准**: 同一模式在不同日期出现不算新洞察
* **L1 容量控制**: 活跃区目标 \< 3000 bytes，最多 12 条导航索引
* **Cron 会话过滤**: session\_search 结果中如果 80%+ 为 Cron 轮次（source="cron"），直接判定无新洞察 → `[SILENT]`。不要尝试从 Cron 输出中提取洞察（信噪比极低）。

### 旧脚本（历史参考，已弃用）

以下脚本仍存在于历史上，但生产环境已切换到 Dream Keeper v2：

```bash
# 旧脚本位置（仅供参考，不推荐在生产中使用）
~/.hermes/workspace/scripts/hermes_dreaming.py
```

如需 dry-run 分析，优先使用 `handler.py --dry-run` 而非旧脚本。

## 数据源

* **会话记录**: `~/.hermes/sessions/*.jsonl`（约 60 个文件，64MB）
* **记忆归档**: `~/.hermes/memories/archive/*.md`
* **L1 索引**: `~/.hermes/memories/MEMORY.md`
* **梦境日志**: `~/.hermes/logs/dreaming/`
* **会话元数据**: `~/.hermes/state.db`（SQLite，sessions 表含 id/source/model/message\_count/input\_tokens/output\_tokens/archived 等字段）
* 扫描技术细节（正则编译、会话去重、用户消息优先）见 [references/scan-techniques.md](references/scan-techniques.md)
* 会话归档标准化流程见 [references/session-archival-workflow.md](references/session-archival-workflow.md)
* **state.db queries** — stat.db session 发现、统计提取、消息读取等实战 SQL 见 [references/state-db-session-queries.md](references/state-db-session-queries.md)
* **MEMORY.md 瘦身策略** — 8KB 阈值操作模板、高价值条目识别标准、备份清理流程见 [references/memory-md-slimdown.md](references/memory-md-slimdown.md)
* **Cron 环境工具限制** — 各工具在 cron 隔离会话中的可用性清单与替代方案见 [references/cron-environment-limits.md](references/cron-environment-limits.md)
* **state.db sessions 表结构**: id(source, user\_id, model, system\_prompt, parent\_session\_id, started\_at, ended\_at, end\_reason, message\_count, tool\_call\_count, input\_tokens, output\_tokens, cache\_read\_tokens, cache\_write\_tokens, reasoning\_tokens, billing\_provider, billing\_base\_url, billing\_mode, estimated\_cost\_usd, actual\_cost\_usd, cost\_status, cost\_source, pricing\_version, title, api\_call\_count, handoff\_state, handoff\_platform, handoff\_error, cwd, rewind\_count, archived, git\_branch, git\_repo\_root) — 归档前先查此表获取统计摘要

## 会话归档操作（state.db + JSONL 双轨）

当需要归档历史会话时，按以下流程执行：

### 步骤 1: 统计当前状态

```python
import sqlite3
conn = sqlite3.connect("/root/.hermes/state.db")
# 查总数、已归档数、活跃数
# 按月份分组统计
# 按来源(source)分组统计
```

### 步骤 2: 标记归档

```sql
UPDATE sessions SET archived = 1 
WHERE started_at < <cutoff_timestamp> 
AND (archived = 0 OR archived IS NULL);
```

### 步骤 3: 清理 JSONL 文件

```bash
# 只删除与归档会话对应的 .jsonl 文件
# 文件名格式: YYYY
```
