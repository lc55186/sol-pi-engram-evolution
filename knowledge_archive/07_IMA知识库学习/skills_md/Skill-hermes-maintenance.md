# Skill-hermes-maintenance

***

name: hermes-maintenance
description: "Hermes 系统维护技能包：MCP服务器故障诊断修复、Profile State.db清理、磁盘/临时文件维护。触发词：MCP修复 / Profile清理 / state.db过大 / 系统维护"
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: \[linux]
metadata:
hermes:
tags: \[hermes, maintenance, mcp, profiles, state.db]
category: ops
-------------

# Hermes Maintenance — 系统维护技能包

> 本 Skill 覆盖 Hermes Agent 自身运维的常见故障模式与修复流程。

## 核心能力

| **能力**              | **触发场景**                                             | **修复方式**                                       |
| ------------------- | ---------------------------------------------------- | ---------------------------------------------- |
| MCP 连接诊断            | `MCP server 'X' tool call failed: Connection closed` | 检查 command 是否为二进制路径而非 `-m` 模块                  |
| SQLite MCP Parking  | `MCP server 'sqlite' ... parking` 警告                 | 进程检查 + 配置验证 + 自动重连                             |
| Profile State.db 清理 | 多 profile 共存导致磁盘占用增长                                 | 归档至 `~/.hermes/archive/profiles/`              |
| 临时文件维护              | `/tmp` 累积旧备份/缓存                                      | `find /tmp -name "*.tar.gz" -mtime +7 -delete` |
| 健康巡检                | 自主维护 cron 每日执行                                       | 磁盘/内存/Cron 成功率检查                               |

## 故障诊断流程

### 1. MCP 连接失败

**症状**：错误日志中出现大量 MCP 连接失败

**排查步骤**：

1. `hermes mcp list` 查看 Transport 列
2. 确认 command 为二进制路径（如 `mcp-server-sqlite`）而非 `python3 -m <module>`
3. 检查 args 参数格式
4. 重启 gateway 或重连 MCP
5. 验证进程运行状态：`ps aux | grep <binary-name>`
   * ⚠️ **注意**：排除 watchdog 父进程（watchdog 启动的子进程算"运行"）
   * 报告格式：`[状态] MCP名称: enabled={bool}, binary={exists}, process={running}`

**参考**：`references/mcp-sqlite-fix-20260811.md`, `references/mcp-sqlite-parking.md`

### 2. Profile State.db 过大

**症状**：磁盘占用持续增长，profiles 目录下 state.db 体积大

**处理流程**：

```bash
# 1. 确认各 profile 状态
du -sh ~/.hermes/profiles/*/state.db 2>/dev/null

# 2. 创建归档目录
mkdir -p ~/.hermes/archive/profiles

# 3. 归档闲置 profile
mv ~/.hermes/profiles/<name>/state.db ~/.hermes/archive/profiles/<name>-state.db.$(date +%Y%m%d)
```

### 3. 临时文件清理

**定期清理规则**：

* `/tmp/*.tar.gz`：`find /tmp -name "*.tar.gz" -mtime +7 -delete`
* Cron 日志：`find ~/.hermes/logs -name "*.log" -mtime +30 -delete`
* **验证**：清理后 `df -h /` 确认空间释放

### 4. SQLite MCP Parking 诊断

**症状**：errors.log 中出现 `MCP server 'sqlite' ... parking` 警告

**诊断流程**：

1. `ps aux | grep mcp-server-sqlite | grep -v grep` → 确认进程存在
2. `grep -A5 "sqlite:" ~/.hermes/config.yaml` → 检查 command 配置
3. `ls -lh ~/.hermes/state.db` → 验证数据库文件
4. `tail -20 ~/.hermes/logs/errors.log | grep sqlite` → 确认 parking 频率

**修复**：

```bash
hermes mcp reload sqlite  # 优先尝试
hermes gateway restart     # 备选方案
```

**影响评估**：

* 不影响核心功能：SQLite MCP 主要用于 session\_search/memory 等工具调用
* cron 任务可能受影响：如果 cron job 使用 sqlite MCP 工具查询 executions.db
* 可暂时忽略：如果主 MCP (如 github, context7) 正常工作

**参考**：`references/mcp-sqlite-parking.md`

## 健康巡检模板

```bash
#!/bin/bash
# 快速健康检查
echo "## 系统健康度"
echo "| 磁盘 | $(df / | tail -1 | awk '{print $5}') |"
echo "| 内存 | $(free | awk '/^Mem:/ {printf "%.0f%%", $3/$2*100}') |"
echo ""
echo "## 已暂停任务"
python3 -c "import json; [print(f\"- {j.get('name')} (ID: {j['id'][:8]})\") for j in json.load(open('/root/.hermes/cron/jobs.json'))['jobs'] if not j.get('enabled')]"
```

**参考脚本**：`scripts/health_audit.sh`

## Pitfalls

| **坑**                    | **症状**                 | **Fix**                                 |                  |
| ------------------------ | ---------------------- | --------------------------------------- | ---------------- |
| MCP command 使用 `-m` 模块   | 连接失败，无明确错误             | 改用二进制路径，查看 `which <command>`            |                  |
| Profile 归档后遗漏 state.db   | 磁盘仍占用高                 | 检查 `ls -lh ~/.hermes/archive/profiles/` |                  |
| 临时文件清理遗漏大文件              | 磁盘持续占用                 | 先 \`du -sh /\* 2>/dev/null              | sort -rh\` 定位大目录 |
| 磁盘清理后未验证                 | 声称清理但实际未释放             | 必须 `df -h /` 二次确认                       |                  |
| SQLite MCP parking 忽略不处理 | cron job 使用 sqlite 时失败 | 按"第4节"流程修复                              |                  |

## 参考

* `references/mcp-sqlite-fix-20260811.md` — MCP SQLite 配置修复案例
* `references/mcp-sqlite-parking.md` — SQLite MCP Parking 故障模式详解
* `scripts/health_audit.sh` — 健康巡检脚本（可复用）
