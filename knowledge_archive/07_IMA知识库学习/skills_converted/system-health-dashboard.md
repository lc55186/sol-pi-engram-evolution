---
name: system-health-dashboard
description: Hermes 全系统评估仪表盘：生成系统概况、已集成项目横向对比、能力雷达图、迭代路线图、健康建议
version: 1.0.0
category: devops
tags: ["evaluation", "dashboard", "health", "metrics", "radar"]
metadata:
  hermes:
    tags: ["evaluation", "dashboard", "health", "metrics", "radar"]
    source: IMA 知识库导入
---

# system-health-dashboard

> Hermes 全系统评估仪表盘：生成系统概况、已集成项目横向对比、能力雷达图、迭代路线图、健康建议。触发词：全面评估 / 系统评估 / 评估报告 / 雷达图 / 全系统检查

# 系统健康仪表盘

## When to Use

* 需要全面评估 Hermes 系统健康度
* 需要横向对比已集成项目
* 需要生成能力雷达图
* 需要迭代路线图和下一步行动建议
* 用户说"全面评估"/"系统评估"/"雷达图"

## 核心功能

### 1. 系统概况统计

* Skill 总数
* Cron 任务数
* 已集成项目数
* 磁盘使用率
* 内存使用
* state.db 大小
* 24h 会话数

### 2. 已集成项目横向对比

跟踪的项目（2026-08-03）：

| **项目**              | **Stars** | **覆盖率** | **状态** |
| ------------------- | --------- | ------- | ------ |
| ECC                 | 20K       | 80%     | ✅      |
| Turbovec            | 14.5K     | 90%     | ✅      |
| Reasonix            | N/A       | 70%     | ✅      |
| book-to-skill       | N/A       | 85%     | ✅      |
| ChatTTS             | 39.5K     | 95%     | ✅      |
| i-have-adhd         | 10K       | 100%    | ✅      |
| Karpathy Guidelines | 197K      | 100%    | ✅      |
| Evolution P0-P2     | N/A       | 85%     | ✅      |
| Evolution P0-P2     | N/A       | 85%     | ✅      |

### 3. 能力雷达图（ASCII 可视化）

8个维度：

* 知识库 (90%)
* 代码质量 (85%)
* 安全审计 (75%→85%)
* 语音合成 (95%)
* 记忆管理 (80%→90%)
* 自动化 (95%)
* 上下文优化 (85%→90%)
* 文档处理 (85%)

综合评分：92/100（+5.8）

### 4. 迭代路线图

* 已完成：7个项目集成 + 自动维护Cron + Evolution方向全部落地
* 进行中：双目录清理、idle-trigger优化
* 待推进：Skill库优化、记忆归档自动化
* **2026-08-03 完成**：
  * P0 MCP分级管理（mcp\_tier\_manager.py）
  * P0 RULES.md合并（统一规则源）
  * P0 上下文压缩策略（context\_compressor.py）
  * P1 跨会话记忆增强（cross\_session\_memory.py）
  * P1 安全审计增强（security\_auditor.py，24规则）
  * P1 按需加载优化（skill\_optimizer.py）
  * P2 进化仪表盘（evolution\_dashboard.py）

### 5. 健康建议

* 磁盘告警 (>90%)
* 数据库膨胀 (>400MB)
* 会话归档需求

## 执行流程

```bash
# 运行评估仪表盘
python3 /root/.hermes/scripts/evaluation_dashboard.py

# 查看报告
cat /root/.hermes/logs/evaluation_report_*.md
```

## 自动调度

| **Cron 任务**                 | **频率**    | **功能** |
| --------------------------- | --------- | ------ |
| weekly-evaluation-dashboard | 每周日 10:00 | 生成评估报告 |

## 输出格式

```
# Hermes 全系统评估报告
**生成时间**: YYYY-MM-DD HH:MM:SS

## 1. 系统概况
[表格]

## 2. 已集成项目横向对比
[表格]

## 3. 能力雷达图
[ASCII可视化]

## 4. 能力维度详情
- **维度** (分数%): 工具列表

## 5. 迭代路线图
[已完成/进行中/待推进]

## 6. 下一步行动建议
[表格]

## 7. 系统健康建议
[告警列表]
```

## 参考

* `scripts/evaluation_dashboard.py` — 评估脚本
* `scripts/evolution_dashboard.py` — 进化仪表盘（监控Skill/脚本/Cron/会话）
* `references/evolution-2026-08-03.md` — 进化方向落地记录
* `~/.hermes/logs/evaluation_report_*.md` — 历史报告

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


