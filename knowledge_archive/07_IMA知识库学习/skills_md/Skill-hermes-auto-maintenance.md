# Skill-hermes-auto-maintenance

***

name: hermes-auto-maintenance
description: "Hermes 全自动维护引擎。自动执行健康检查、修复、归档、压缩等维护任务。触发词：自动维护 / 系统健康 / 会话归档 / 数据库压缩 / cron 自动修复"
version: 1.0.0
author: Hermes
tags: \[maintenance, automation, health, self-heal]
---------------------------------------------------

# Hermes Auto-Maintenance Engine

## 概述

全自动维护引擎，每日运行两次，自动检测并修复系统问题。

## 检查项

| **检查项**         | **阈值**                     | **动作**                  |
| --------------- | -------------------------- | ----------------------- |
| 活跃会话数           | >300                       | 自动归档最老会话                |
| state.db 大小     | >400MB                     | 执行 VACUUM               |
| 嵌套 skills 目录    | 存在                         | 清除嵌套                    |
| SKILL.md 缺 name | >0                         | 补充 frontmatter          |
| 模型配置漂移          | hermes config 与 MEMORY 不一致 | 自动修复（见 Pitfalls）        |
| fail2ban 自动封禁失效 | 高频攻击 IP 未封禁                | 手动封禁（见 honeyport skill） |

## 脚本

路径：`/root/.hermes/scripts/auto_maintain.py`

```bash
python3 /root/.hermes/scripts/auto_maintain.py
```

## Cron

每 12 小时运行一次（00:00 和 12:00）。

## 报告

写入 `~/.hermes/logs/auto_maintain/report_<YYYYMMDD>.json`

## 参考

* [2026-08-11 维护记录](references/2026-08-11-maintenance-run.md)

## 参考

* [2026-08-11 维护记录](references/2026-08-11-maintenance-run.md)

## Pitfalls

| **坑**              | **症状**                   | **Fix**                                                                                       |
| ------------------ | ------------------------ | --------------------------------------------------------------------------------------------- |
| state.db VACUUM 超时 | 大库 VACUUM 超过脚本超时         | 手动执行：`sqlite3 ~/.hermes/state.db "VACUUM;"`                                                   |
| MEMORY.md 检索失效     | `Facts found: 0`         | 运行 memory-injection-fix skill                                                                 |
| cron enabled: 0    | cron 列表为空                | 正常现象，用 `hermes cron list --all` 检查                                                            |
| 数据库 \<400MB        | VACUUM 跳过                | 372.7 MB 时跳过，\<300 MB 再执行                                                                     |
| 模型配置漂移             | `hermes status` 显示不同主力模型 | 执行 `hermes config set model <name>` + `hermes config set provider <provider>`，对比 MEMORY 确认目标值 |
| fail2ban 自动封禁失效    | 高频攻击 IP 未封禁              | 检查 `fail2ban-client status sshd`，手动执行 `fail2ban-client set sshd banip <IP>`                   |

## 步骤

1. **读取当前配置** — 查看现有设置
2. **应用变更** — 修改配置项
3. **验证生效** — 确认变更已生效
4. **回滚准备** — 保留恢复方案

## 验证

- [ ] 配置变更已保存

- [ ] 服务/功能按预期工作

- [ ] 无副作用影响其他组件
