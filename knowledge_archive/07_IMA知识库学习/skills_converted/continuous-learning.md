---
name: continuous-learning
description: 构建 Hermes Agent 自我进化闭环：会话观察→模式提取→效果监测→分阶段学习计划
version: 1.0.0
category: imported
tags: ["learning", "self-improvement", "observer", "monitor", "planning"]
metadata:
  hermes:
    tags: ["learning", "self-improvement", "observer", "monitor", "planning"]
    source: IMA 知识库导入
---

# continuous-learning

> 构建 Hermes Agent 自我进化闭环：会话观察→模式提取→效果监测→分阶段学习计划。触发词：学习引擎 / 持续学习 / 自我进化 / Phase 2

# Continuous Learning Pipeline

> 为 Hermes Agent 构建自我进化的闭环系统：观察→提取模式→置信度评分→持久化→效果监测。

## 触发条件

* 用户要求检查/优化学习引擎或自我提升流程
* 需要建立自动化学习效果追踪机制
* Phase 1 单主题训练完成后进入 Phase 2+ 跨主题整合阶段
* 用户说"学习引擎"、"持续学习"、"自我进化"、"Phase 2"

## 核心架构

```
┌─────────────────────────────────────────────────────┐
│                    Learning Pipeline                  │
├──────────┬──────────┬──────────┬────────────────────┤
│ Observer │ Monitor  │ Planner  │ Tracker            │
│ 会话观察  │ 效果评估  │ 阶段规划  │ 进度追踪            │
└──────────┴──────────┴──────────┴────────────────────┘
```

### 1. Observer — 行为模式提取

从最近会话中提取用户工作模式，生成可复用的 instinct（本能）。

**脚本位置**: `/root/.hermes/scripts/learning_observer.py`

**关键步骤**:

1. 确保目录存在: `mkdir -p ~/.hermes/learning/observer/instincts`
2. 运行: `python3 /root/.hermes/scripts/learning_observer.py`
3. 获取统计: `python3 /root/.hermes/scripts/learning_observer.py stats`

**数据库 schema 注意**: messages 表使用 `timestamp` (REAL) 字段，不是 `created_at`。查询时用 `WHERE timestamp > ?` 配合 `.timestamp()` 值。

**提取的模式类型**:

* `heavy-tool-user`: 复杂任务中频繁调用工具 (>3次)
* `proactive-debugger`: 遇到错误先查根因再修复
* `devops-oriented`: 构建应用时包含部署/容器化

### 2. Monitor — 效果监测与雷达图

定期评估学习效果，生成能力雷达图和测试通过率统计。

**脚本位置**: `/root/.hermes/scripts/learning_monitor.py`

**输出报告路径**: `~/.hermes/learning/reports/day31_day60/Weekly_Monitor_YYYYMMDD.md`

**评估维度**:

* 项目健康度 (含测试/文档比例)
* 测试通过率 (py\_compile + pytest)
* Observer 识别的模式数量和置信度分布
* 6 维能力雷达图 (逆向工程/Java/Python/前端Flutter/运维安全/系统设计)

### 3. Planner — 分阶段学习计划

**Phase 1** (Day 1-30): 单主题深度训练 — 每个领域 6 个 Module

**Phase 2** (Day 31-60): 全栈整合 — 跨主题综合项目

**计划文件**: `~/.hermes/learning/phase2_plan.md`

### 4. Tracker — 进度追踪

**文件位置**: `~/.hermes/learning/progress/learning_tracker.md`

每次更新时需同步修改当前学习日和历史归档。

## Cron 自动化

已配置的 cron 任务:

* **learning-observer-weekly** (周日 01:00): 行为模式提取 + 统计
* **learning-effectiveness-monitor** (周一/四 02:00): 能力雷达图 + 测试报告

## 输出格式

Observer 输出 JSON:

```json
{
  "patterns": [{"id": "...", "confidence": 0.7, "domain": "debugging"}],
  "stats": {"total": N, "avg_confidence": X}
}
```

Monitor 输出周报 Markdown，包含表格和雷达图评级。

## Pitfalls

* **schema 不匹配**: messages 表用 `timestamp` (REAL)，不是 `created_at` (TEXT)。查询时必须用 `.timestamp()` 转换时间。
* **state.db 路径**: 可能是 `~/.hermes/state.db` 而非 `~/.hermes/data/state.db`，使用前确认。
* **sqlite3 CLI 缺失**: 环境通常没有 sqlite3 命令行工具，必须用 python3 -c 或脚本操作。
* **Phase 2 项目目录可能不存在**: `applications/comprehensive/` 在 Phase 2 启动前为空，monitor 应优雅处理。

## 步骤

1. **接收输入** — 确认输入参数和上下文
2. **执行处理** — 完成核心任务
3. **返回结果** — 输出处理结果

## 验证

- [ ] 任务目标已达成

- [ ] 输出格式正确

- [ ] 错误情况已处理


