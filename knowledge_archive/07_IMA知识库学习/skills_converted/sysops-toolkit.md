---
name: sysops-toolkit
description: 系统运维自动化工具包
version: 1.0.0
category: devops
tags: ["运维", "监控", "备份", "日志", "性能", "Linux"]
metadata:
  hermes:
    tags: ["运维", "监控", "备份", "日志", "性能", "Linux"]
    source: IMA 知识库导入
---

# sysops-toolkit

> 系统运维自动化工具包。集成健康检查、日志分析、自动备份、性能监控、RAG文档预处理等运维脚本。当用户需要系统运维、性能监控、日志分析、备份管理、文档解析、安全加固、远程部署验证、全栈服务检查、会话归档时使用。

# 系统运维自动化工具包

## 快速命令

### 系统健康检查

```bash
~/.hermes/skills/sysops-toolkit/scripts/health_check.sh
~/.hermes/skills/sysops-toolkit/scripts/health_check.sh --json
```

### 日志分析

```bash
~/.hermes/skills/sysops-toolkit/scripts/log_analyzer.sh [日志文件] [输出报告] [时间范围]
```

### 自动备份

```bash
~/.hermes/skills/sysops-toolkit/scripts/auto_backup.sh [源目录] [目标目录]
~/.hermes/skills/sysops-toolkit/scripts/auto_backup.sh /etc /backup --encrypt
```

### RAG 文档预处理

```bash
# PDF/Word/PPT/MD → 结构化 JSON（LiteParse 优先，降级到 markitdown）
bash scripts/liteparse_rag_pipeline.sh <input_dir> <output_dir>
```

### 系统巡检

```bash
/root/scripts/sys_inspector.py          # 快速巡检
/root/scripts/sys_inspector.py --deep   # 深度巡检（含 Hermes/网络检查）
/root/scripts/sys_inspector.py --json   # JSON 输出
```

### 会话归档（推荐）

使用 `sqlite_query.py` 脚本（`/root/.hermes/scripts/sqlite_query.py`）：

```bash
# 统计
python3 /root/.hermes/scripts/sqlite_query.py /root/.hermes/state.db "SELECT COUNT(*), SUM(CASE WHEN archived=1 THEN 1 ELSE 0 END), SUM(CASE WHEN archived=0 THEN 1 ELSE 0 END) FROM sessions"

# 归档 >30天会话
python3 /root/.hermes/scripts/sqlite_query.py /root/.hermes/state.db "UPDATE sessions SET archived=1 WHERE started_at < ?" "$(python3 -c 'import time; print(int(time.time()-2592000))')"
```

详见 `cron-reliability` skill。

### FTS 存储优化（老用户瘦身 state.db）

老用户（schema v22 及更早）的 state.db 因 inline FTS + trigram 包含 tool 行噪声，可能膨胀到数 GB 甚至数十 GB。

详见 [`references/state-db-optimization.md`](references/state-db-optimization.md)。

**快速检测**：

```bash
python3 -c "
from pathlib import Path; import sys; sys.path.insert(0, '/root/hermes-agent')
from hermes_state import SessionDB
db = SessionDB(db_path=Path('/root/.hermes/state.db'))
print(f'Optimize available: {db.fts_optimize_available()}')
cur = db._conn.execute('SELECT page_count * page_size / 1024 / 1024 FROM pragma_page_count(), pragma_page_size()')
print(f'DB size: {cur.fetchone()[0]:.1f} MB')
db.close()
"
```

**执行优化**：`SessionDB.optimize_fts_storage(progress_cb=..., vacuum=True)`（可能需要数分钟，低峰期执行）。

## 知识库完整性检查

完整流程见 [`references/knowledge-base-integrity-check.md`](references/knowledge-base-integrity-check.md)。Cron 执行模板见 [`references/knowledge-backup-cron-workflow.md`](references/knowledge-backup-cron-workflow.md)。核心步骤：

```python
# 统计技能总数（精确计数用 */SKILL.md 模式）
search_files(target='files', pattern='*/SKILL.md', path='/root/.hermes/skills')
# 统计脚本数（递归子目录用 **/*.py 模式）
search_files(target='files', pattern='**/*.py', path='/root/.hermes/scripts')
# 统计 References（*/references/* 模式，结果可能 capped 到 200）
search_files(target='files', pattern='references/*', path='/root/.hermes/skills')
# 关键技能用 read_file 二次确认
```

⚠️ `search_files` 对 `pattern='SKILL.md'` 可能只返回 50 条（旧版默认 limit）。**精确计数**用 `pattern='*/SKILL.md'` 或 `pattern='**/SKILL.md'`，实测可从 50→129。结果被 cap 时用 offset/limit 分页或换更细的 glob 模式。

⚠️ References 计数是从文件路径中**去重**出唯一目录数，不是文件数。多个技能共享 references/ 目录时需逐一验证。

## 使用场景

| **场景** | **命令**                                                | **说明**                                              |
| ------ | ----------------------------------------------------- | --------------------------------------------------- |
| 日常检查   | `health_check.sh`                                     | CPU/内存/磁盘/负载/网络                                     |
| 远程部署验证 | `references/remote-server-verification.md` 中的完整栈检查命令链 | Java/Spring Boot/Nginx/MySQL/Valkey/Node.js 多服务健康检查 |
| 日志排查   | `log_analyzer.sh /var/log/syslog`                     | 错误统计+时间线                                            |
| 定期备份   | `auto_backup.sh /etc /backup`                         | 增量备份+硬链接                                            |
| RAG 管道 | `liteparse_rag_pipeline.sh ./docs ./json_out`         | 文档→结构化JSON                                          |
| 性能基线   | `health_check.sh --json`                              | JSON 输出便于集成                                         |
| 策略对比   | `ab_test_runner.sh "name" "a" "b"`                    | A/B 测试                                              |
| 记忆健康   | `semantic_stability_check.sh`                         | 语义稳定性验证                                             |
| 知识库审计  | 见 `references/knowledge-base-integrity-check.md`      | 技能/脚本/引用盘点                                          |
| 会话归档   | Python sqlite3 模块操作 state.db                          | 标记归档 + 清理 JSONL 文件                                  |

## 知识库

* 知识索引: `references/knowledge_index.md`
* [错误日志分诊](references/error-log-triage.md) — errors.log 三步分诊法、时效过滤、告警规则
* [自进化模式](references/self-evolution-patterns.md) — 决策日志/版本快照/语义验证/A/B测试/权限分级

### 运维仪表盘快速部署

详见 `references/ops-panel-deployment.md` — Node.js + ECharts 暗色主题运维面板（/proc读取替代exec）

### 远程服务器 SSH 批量验证

详见 `references/remote-server-verification.md` — sshpass + SSH 自动化服务状态检查（Java/Nginx/MySQL/Valkey/Node.js），附 HTTP 探测清单和结果解读模板。含 Java Spring Boot 全栈深度检查模板（资源/进程/端口/路由/Git/日志/JVM/运维面板）

* [安全评分模型](references/security-dashboard-pattern.md) — 100分基准加权扣分（CPU/内存/SSH/防火墙）
* 完整学习产出: `~/.hermes/learning/knowledge/KNOWLEDGE_sysops_M1-M5.md`
* **scripts/sys\_inspector.py** — 统一系统巡检脚本（30分钟cron），6大维度检查，异常时输出中文告警，正常静默
* **references/state-db-sessions-schema.md** — state.db sessions 表完整 schema + 常用归档查询
* **references/state-db-optimization.md** — state.db FTS 存储优化：从 inline 模式迁移到外部内容模式 + trigram tool 行排除，节省 40-75% 磁盘空间
* **references/knowledge-base-rag-status.md** — 知识库/RAG 基础设施现状与使用指南

## 已知 Pitfalls

### 系统巡检脚本：ps aux 自身被误报为高CPU进程

`sys_inspector.py` 中使用 `ps aux --sort=-%cpu` 检测高CPU进程时，该命令自身会被排在第一位并误报为100% CPU。**修复**：在判断前过滤掉包含 `ps aux`、`sort=-%cpu`、`tail -n`、`head -`、`awk` 等管道/自身关键词的进程行。见脚本第88-

## 触发条件

系统运维自动化工具包。集成健康检查、日志分析、自动备份、性能监控、RAG文档预处理等运维脚本。当用户需要系统运维、性能监控、日志分析、备份管理、文档解析、安全加固、远程部署验证、全栈服务检查、会话归档时使用。
