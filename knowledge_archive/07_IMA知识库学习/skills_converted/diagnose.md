---
name: diagnose
description: 硬 bug 和性能回退的纪律性诊断循环：复现→缩小→假设→插桩→修复→回归测试
version: 1.0.0
category: devops
tags: ["diagnose", "debug", "bug", "performance", "troubleshooting"]
metadata:
  hermes:
    tags: ["diagnose", "debug", "bug", "performance", "troubleshooting"]
    source: IMA 知识库导入
---

# diagnose

> 硬 bug 和性能回退的纪律性诊断循环：复现→缩小→假设→插桩→修复→回归测试。 触发词：diagnose this / debug this / 诊断 / 调试 / 修bug / 排查。 适用：服务崩溃、API报错、性能下降、内存泄漏、间歇性故障。 反例：不要触发于新功能开发、代码审查、部署操作。

# Diagnose — 纪律性诊断循环

> 硬 bug 和性能回退的纪律性诊断：Reproduce → Minimise → Hypothesise → Instrument → Fix → Regression-test.

## Communication Style

* **语言**：中文为主，技术术语保留英文
* **结构**：Phase 顺序推进，每 Phase 有明确输入/输出，不跳步
* **语气**：纪律性、系统性，拒绝猜测，强调"先查后做"
* **受众**：需要系统性排查故障的运维/开发者
* **禁忌**：不在没有复现信号的情况下开始假设，不编造日志
* **特殊原则**：先搜后做 — 安装/配置/调试前先 web\_search 查文档

## Success Criteria

- [ ] Phase 1：建立了可用的反馈循环（failing test / curl / CLI 等）

- [ ] Phase 2：成功复现了用户描述的故障

- [ ] Phase 3：生成了 3-5 个可证伪的假设并排序

- [ ] Phase 4：每个探针对应一个假设预测

- [ ] Phase 5：回归测试通过（或记录了缺失的测试 seam）

- [ ] Phase 6：清理了所有 [DEBUG-...] 标记，输出了 post-mortem

- [ ] Verdict 明确：RESOLVED / PARTIAL / BLOCKED

## When to Use

* 用户说"diagnose this"、"debug this"、"诊断"、"调试"、"修bug"、"排查"
* 服务崩溃、API 报错、性能下降、内存泄漏
* 间歇性故障难以复现
* 用户描述某个东西"坏了"、"报错了"、"跑不动了"

**不要触发于：** 新功能开发、代码审查、部署操作。

## Prerequisites

- [ ] 有终端权限（所有诊断操作都需要）

- [ ] 能访问相关日志和代码

- [ ] 知道故障现象（用户描述或错误信息）

如果无法复现故障或无法访问环境，**停下来问用户要什么**。

## Common Diagnostic Patterns

### System Status Checks

* Verify service health and logs
* Check resource utilization (CPU, memory, disk)
* Validate configuration files
* **Check for systemd service scope conflicts** — if a service shows `code=killed, status=9/KILL` with rapid restart loops, check whether both user-level (`systemctl --user`) and system-level (`systemctl`) services exist for the same unit. See [references/systemd-service-conflicts.md](references/systemd-service-conflicts.md).

### PHP-FPM + Nginx "Access denied" Diagnosis

When an API endpoint returns "Access denied" or blank 200, diagnose in this order:

1. **File ownership** — PHP-FPM runs as `apache` user; files written by `write_file`/`patch` tools become `root:root`. Run `chown apache:apache /var/www/html/api/*.php` after every file modification.
2. **PHP-FPM pool config** — check `listen.acl_users` includes `nginx`, `security.limit_extensions` includes `.php`.
3. **Nginx routing** — verify `fastcgi_pass` matches PHP-FPM `listen` address, `SCRIPT_FILENAME` points to correct file.
4. **SELinux** — `getenforce` + `ls -Z` to check context.
5. **PHP error log** — `tail /var/log/php-fpm/www-error.log` for SQL errors, permission denied, etc.
6. **Database auth** — `mysql -u root` to verify credentials match config.

**Key pattern**: Use `extractAction()` + `REQUEST_URI` for dynamic routing instead of `switch($path)` exact matching — Nginx location regex passes the action segment as-is, which rarely matches hardcoded paths. See `sysops-automation/references/php-fpm-nginx-api-debug.md` for full details.

### SSH Connection Diagnostics

* Test network connectivity with ping
* Verify SSH port accessibility with nc/nmap
* Check SSH authentication methods (password, key, publickey)
* Handle expect-based password automation when direct SSH fails
* Use Python paramiko as fallback for complex authentication scenarios
* Document connection failure patterns and resolution strategies

### Timezone Mismatch in Date Queries

* Symptom: cron job returns empty results, manual run works fine; or "yesterday" query misses data
* Root cause: DB stores UTC timestamps, script uses local timezone for date math
* Fix: use timestamp range queries (`started_at >= epoch_start AND started_at < epoch_end`) instead of string prefix matching (`id LIKE '20260617%'`)
* Full pattern and real case: [references/timezone-mismatch-debugging.md](references/timezone-mismatch-debugging.md)

### Hermes 模型调用全景审计

当用户要求"模型调用全景"、"完整诊断报告"、"模型审计"时，加载 [references/hermes-model-audit.md](references/hermes-model-audit.md) 并按其中的审计清单执行。覆盖：枚举 profile → 读配置 → 读 .env → 测试所有 API 端点 → 查看 fallback 逻辑 → 输出拓扑图。

### Druid 连接池 pollLast() 无限等待

* Symptom: 服务启动后日志停在 Quartz/Mapper 初始化，端口不起；`jcmd Thread.print` 显示主线程在 `com.alibaba.druid.pool.DruidDataSource.pollLast()` 等待
* Root cause: Druid 创建初始连接失败（密码/认证/时区），但不抛异常而是进入 `pollLast()` 等待可用连接
* Diagnosis: `jcmd <PID> Thread.print` → 看 main 线程 stack → 确认是 `pollLast` → 检查 MySQL `SHOW PROCESSLIST` → 验证密码/时区/认证
* Fix: 修 MySQL 密码、`serverTimezone=Asia/Shanghai`（替代 `GMT%2B8`）、Redis 密码匹配
* Full pattern and real case: [source-deploy-restricted-env/references/druid-mysql-connection-pool-hang-debug.md](/root/.hermes/skills/devops/source-deploy-restricted-env/references/druid-mysql-connection-pool-hang-debug.md)

When exploring the codebase, use the project's domain glossary to get a clear mental model of the relevant modules, and check ADRs in the area you're touching.

## Phase 1 — Build a feedback loop

**This is the skill.** Everything else is mechanical. If you have a fast, deterministic, agent-runnable pass/fail signal for the bug, you will find the cause — bisection, hypothesis


