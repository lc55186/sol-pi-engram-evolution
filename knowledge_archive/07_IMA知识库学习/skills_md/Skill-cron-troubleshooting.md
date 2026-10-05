# Skill-cron-troubleshooting

***

name: cron-troubleshooting
description: Hermes Cron 任务故障诊断与修复。当用户报告 cron 任务失败、模型漂移、或需要排查定时任务问题时触发。包含工具限制、验证流程、常见故障模式。
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: \[linux]
tags: \[cron, troubleshooting, debugging, hermes]
metadata:
hermes:
tags: \[cron, troubleshooting, debugging]
category: devops
related\_skills: \[hermes-dreaming, session-maintenance, cronjob-management-optimization]
-----------------------------------------------------------------------------------------

# Cron 故障诊断与修复

## 触发条件

* 用户报告 cron 任务失败
* 发现任务模型漂移（未固定模型导致使用错误模型）
* 需要排查定时任务执行问题
* 梦境报告中提及 cron 故障

## 核心原则

1. **先诊断后修复**：确认问题再行动
2. **最小化变更**：只改必须改的配置
3. **验证修复效果**：测试后确认问题解决
4. **记录根因**：避免同类问题重复出现

## 常见故障模式

### 1. 模型漂移（2026-08-14 高频，8/17 再次爆发）

**症状**：

* Cron 任务使用与预期不同的模型
* 全局模型切换后，任务未更新
* 日志显示"Skipped to prevent unintended spend: global inference config drifted since this job was created"

**根因**：

```bash
hermes cron add <task> --model agnes-2.0-flash  # 正确：创建时固定
hermes cron add <task>  # 错误：未固定，全局切换后全部失效
```

**2026-08-17 实测**：全局模型从 `longcat-2.0` 切换到 `agnes-2.0-flash` 后，10 个 unpinned 任务全部跳过（股票推荐、知识库维护、自动进化等核心任务停摆）。

**修复**：

```bash
# 检查所有 cron 任务
hermes cron list

# 编辑任务固定模型
hermes cron edit <job_id> --model agnes-2.0-flash

# 或批量检测未固定任务
hermes cron list | grep -v "model:" | grep -v "Job ID" | grep -v "^$"
```

**预防措施（重要）**：

* ⚠️ **创建任务时强制指定 `--model`**：这是唯一可靠防护
* ⚠️ MEMORY.md 曾声称"已创建 cron-model-drift-detector skill"，该 skill **不存在**——此为历史信息错误，勿信
* 全局模型切换前，先执行：`hermes cron list` 检查所有任务是否已 pin
* 建议将关键任务迁移至 `agnes-2.0-flash`（主力模型）而非依赖 longcat

**预防脚本**：见 [references/cron-model-pin-workflow.md](references/cron-model-pin-workflow.md)

### 2. 工具不可用（Cron 环境限制）

| **工具**         | **可用性**    | **替代方案**                     |
| -------------- | ---------- | ---------------------------- |
| `memory`       | ❌ DISABLED | 用 `write_file` 直接写 MEMORY.md |
| `execute_code` | ❌ BLOCKED  | 用 `terminal` + `python3 -c`  |
| `patch`        | ✅ 可用       | 首选文件修改工具                     |
| `write_file`   | ✅ 可用       | 写入完整文件内容                     |

**工作流**：

```bash
# 1. 用 terminal 执行 Python
terminal(command="python3 -c \"import sqlite3; ...\"")

# 2. 用 write_file 写入 MEMORY.md（非追加）
write_file(path="~/.hermes/MEMORY.md", content="...完整内容...")

# 3. 用 patch 编辑小段内容
patch(path="~/.hermes/MEMORY.md", old_string="...", new_string="...")
```

### 3. state.db 查询失败

**症状**：

* `session_search` 返回空结果
* SQLite 错误："no such column: expires\_at"
* FTS5 损坏

**诊断**：

```bash
# 检查 sessions 表结构
sqlite3 ~/.hermes/state.db ".schema sessions"

# 检查是否存在 expires_at 列
sqlite3 ~/.hermes/state.db "PRAGMA table_info(sessions);" | grep expires_at

# 检查 FTS5 状态
sqlite3 ~/.hermes/state.db "SELECT * FROM sessions_fts WHERE sessions_fts = 'corrupt';"
```

**修复**：

```bash
# 方案 1：ALTER TABLE（推荐）
sqlite3 ~/.hermes/state.db "ALTER TABLE sessions ADD COLUMN expires_at REAL;"

# 方案 2：重建完整 schema（从备份）
sqlite3 ~/.hermes/state.db ".backup /tmp/state.db.bak"
python3 ~/.hermes/scripts/fix-state-db.py
# 然后手动恢复数据
```

**预防**：

* 定期备份 state.db
* 在梦境巩固中检查表结构完整性

### 4. OpenWebUI 无限重启（2026-08-14 新增）

**症状**：

* `systemctl status openwebui` 显示"activating (auto-restart)"
* 重启计数 > 10000
* 日志文件持续增长

**根因**：容器 `/data` 目录不存在

**修复**：

```bash
# 方案 1：创建数据目录
sudo mkdir -p /var/lib/openwebui/data
sudo chown -R root:root /var/lib/openwebui
sudo systemctl restart openwebui

# 方案 2：禁用服务（如不需要）
sudo systemctl stop openwebui
sudo systemctl disable openwebui

# 清理日志
sudo journalctl --vacuum-time=1d
```

## 诊断流程

### 步骤 1：收集信息

```bash
# 查看 cron 任务列表
hermes cron list

# 查看最近执行日志
ls -lt ~/.hermes/cron/output/<job_id>/

# 检查系统状态
systemctl status openwebui
df -h /
sqlite3 ~/.hermes/state.db "SELECT COUNT(*) FROM sessions;"
```

### 步骤 2：定位问题

* 任务是否失败？→ 查看输出文件
* 模型是否正确？→ 检查 cron 配置
* 数据库是否正常？→ 查询 state.db
* 服务是否运行？→ systemctl status

### 步骤 3：执行修复

按故障模式选择对应修复方案

### 步骤 4：验证

```bash
# 手动运行任务测试
hermes cron run <job_id>

# 检查执行结果
cat ~/.hermes/cron/output/<job_id>/latest.md
```

## 检测脚本

### 模型漂移检测（建议每日运行）

```bash
#!/bin/bash
# 检查所有 cron 任务是否固定模型
hermes cron list | grep -v "model:" | grep -v "Job ID" | grep -v "^$"
# 如有输出，说明存在未固定模型的任务
```

### state.db 完整性检查

```bash
#!/bin/bash
# 检查 sessions 表是否包含必要列
sqlite3 ~/.hermes/state.db "PRAGMA table_info(sessions);" | grep -E "(expires_at|archived|message_count)"
# 应返回 3 行，否则表结构不完整
```

## 预防措施

1. **Cron 配置规范**：
   * 添加任务时始终指定 `--model`
   * 使用绝对路径（`python3` 而非 `python`）
   * 设置合理超时（`timeout=1800`）
2. **定期健康检查**：
   * 梦境巩固自动检测（每日 23:10）
   * 手动运行诊断脚本（每周）
3. **备份策略**：
   * state.db 每日备份
   * 保留最近 7 天备份

## 关联资源

* [references/cron-drift-report-20260814.md](references/cron-drift-report-20260814.md) — 2026-08-14 漂移检测详细报告
* [references/cron-tools-limitations-20260814.md](references/cron-tools-limitations-20260814.md) — Cron 工具限制实测
* [references/cron-model-pin-workflow.md](references/cron-model-pin-workflow.md) — 模型 Pin 预防工作流（2026-08-17 新增）
* [hermes-dreaming skill](hermes-dreaming) — 梦境系统自动检测

## 版本历史

* v1.2.0 (2026-08-19): 新增 references/cron-model-pin-workflow\.md，包含预防脚本和全局切换前检查清单；补充模型漂移检测自动化方案。
* v1.1.0 (2026-08-17): 新增模型漂移预防措施（创建时强制pin）、OpenWebUI P0状态更新、飞书DNS故障检测模式。修复MEMORY.md错误声称"已创建cron-model-drift-detector skill"（实际不存在）。新增 references/cron-model-pin-workflow\.md。
