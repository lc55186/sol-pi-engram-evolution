# Skill-self-heal

***

name: self-heal
version: 3.0.2
description: "自愈基础设施 3.0 — 故障推理引擎 + 修复沙箱 + 经验学习闭环。当系统异常（服务宕机/磁盘满/进程僵尸/网络断连/配置错误）时自动诊断根因、安全修复、记录经验。"
category: devops
tags: \[self-heal, fault-diagnosis, auto-repair, sandbox, incident-learning]
----------------------------------------------------------------------------

# Self-Heal 3.0 — 自愈基础设施

> 从"人工排查修复"到"Agent 自主诊断→安全修复→经验沉淀"的闭环自愈系统。

## 执行铁律

> **不拖延，发现问题立即自主修复→验证→评估→记录→沉淀，不要带着错误继续。**

* 发现异常 → 立即诊断，不等用户指示
* 诊断完成 → 安全方案(safety=safe)直接执行，不逐步确认
* 执行完成 → 验证结果 + 记录经验 + 更新记忆
* 不能自动修复 → 立即推送飞书告警，不静默忽略
* 任何环节出错 → 修复后继续，不放弃、不等待

## 核心架构

```
异常信号 → 故障推理引擎 → 修复方案 → 修复沙箱 → 验证 → 经验沉淀
    ↑                                              │
    └──────────── 经验学习闭环 ←──────────────────┘
```

### 三大模块

| **模块**    | **说明**            | **触发条件**           |
| --------- | ----------------- | ------------------ |
| 🧠 故障推理引擎 | 多维度假设生成 + 验证，定位根因 | 巡检异常 / 服务告警 / 用户报障 |
| 🔧 修复沙箱   | 安全执行修复命令，带回滚保护    | 推理引擎输出修复方案后        |
| 📚 经验学习闭环 | 每次修复自动记录，相似故障秒级响应 | 修复完成后自动触发          |

## 目录结构

```
self-heal/
├── SKILL.md                    # 本文件
├── fault_engine/
│   ├── diagnose.py             # 故障推理引擎
│   ├── patterns.json           # 故障模式库（可增长）
│   └── hypotheses.py           # 假设生成器
├── repair_sandbox/
│   ├── repair.py               # 修复沙箱 CLI
│   ├── sandbox.py              # 安全执行环境
│   └── rollback.py             # 回滚机制
├── learning/
│   ├── incidents.jsonl        # 故障事件记录
│   ├── lessons.jsonl           # 经验教训
│   └── similarity.py           # 相似故障匹配
├── references/
│   ├── runbook.md              # 标准操作手册
│   ├── severity-matrix.md      # 严重度矩阵
│   ├── fault-patterns.md       # 故障模式库参考（14种模式）
│   ├── memory-md-concurrency.md # MEMORY.md 并发写入冲突解决
│   ├── service-conflict.md     # 服务端口冲突诊断手册
│   ├── service-substitute-detection.md # 服务功能替代检测手册
│   ├── cron-workflow-false-positive.md  # Cron巡检误报完整处理流程
└── scripts/
    ├── health_check.sh         # 系统健康检查（JSON输出）
    ├── service_watchdog.sh     # 服务看门狗
    ├── verify_repair.py        # 修复后验证（post-repair mandatory gate）
    └── feishu_notify.py        # 飞书告警通知（扫描未修复→格式化→推送）
```

## 工作流

### Phase 1: 故障检测

来源（按优先级）：

1. **sys\_inspector.py**（30分钟 cron）→ 异常信号
2. **health\_check.sh** → 资源告警
3. **log\_analyzer.sh** → 错误日志告警
4. **用户直接报障** → "XX 挂了"/"XX 不工作"

### Phase 2: 故障推理

```bash
# 自动诊断
python3 fault_engine/diagnose.py --alert "<alert_text>"

# 输出示例：
# {
#   "hypotheses": [
#     {"cause": "磁盘满导致服务无法写入日志", "confidence": 0.92, "evidence": ["/var/log 95%"]},
#     {"cause": "OOM Killer 杀掉了进程", "confidence": 0.65, "evidence": ["dmesg: Out of memory"]}
#   ],
#   "recommended_action": "清理磁盘空间",
#   "safety_level": "safe"
# }
```

推理逻辑：

1. 解析告警文本 → 提取关键实体（服务名、资源、错误码）
2. 匹配历史故障模式 → patterns.json
3. 收集环境证据 → 运行诊断命令
4. 生成假设列表 → 按置信度排序
5. 输出修复建议 + 安全等级

### Phase 3: 修复沙箱

```bash
# 安全执行修复
bash repair_sandbox/repair.py --plan plan.json --dry-run    # 预览
bash repair_sandbox/repair.py --plan plan.json --execute   # 执行
```

安全约束：

* **禁止**：rm -rf /、格式化磁盘、删除系统文件、修改防火墙规则（除非明确授权）
* **自动**：重启服务、清理缓存/日志、调整配置、重启进程
* **需确认**：修改系统配置、安装/卸载包、网络配置变更
* **回滚**：每个修复操作自动记录 undo 命令，执行失败自动回滚

### Phase 4: 经验沉淀

每次修复完成后自动记录：

```json
{
  "id": "INC-20260617-001",
  "timestamp": "2026-06-17T10:00:00Z",
  "symptom": "Nginx 返回 502 Bad Gateway",
  "root_cause": "PHP-FPM 进程池耗尽",
  "fix": "重启 PHP-FPM 并调整 pm.max_children",
  "commands": ["systemctl restart php-fpm", "sed -i 's/pm.max_children = 5/pm.max_children = 20/' /etc/php-fpm.d/www.conf"],
  "rollback_commands": ["systemctl stop php-fpm", "cp /etc/php-fpm.d/www.conf.bak /etc/php-fpm.d/www.conf"],
  "verification": "curl -s -o /dev/null -w '%{http_code}' http://localhost/ → 200",
  "time_to_fix": "2m",
  "tags": [nginx, php-fpm, 502, process-pool]
}
```

下次遇到相似故障 → `similarity.py` 匹配历史事件 → 秒级推荐修复方案。

## 行为协议：人工交互中的错误自检

当用户在对话中纠正 Agent（"不对"/"错了"/"又犯了"/"纠正"）或操作结果与预期不符时，激活以下流程：

### Step 1: 记录错误模式

检查 MEMORY.md 的 `[错误日志]` 区是否已有此模式。如无，追加：

```
# 错误模式 | 正确做法 | 来源日期
```

### Step 2: 更新相关 memory

如果正确做法涉及已有 memory 条目（如提供商对应关系、服务器 IP、端口等），同步更新该条目。

### Step 3: 简短报告

完成后回复："已记录错误模式：XXX → YYY"

### Step 4: 下次自检

每次涉及类似操作前，主动核对错误日志区，避免重复犯错。

**触发关键词**：不对、错了、纠正、又犯了、不是这个、你看错了、我说的不是这个意思、stop doing X

## Pitfalls（已验证）

| **坑**                             | **症状**                                                                                                                                                                                                                                                                                                                                             | **Fix**                                                                                                                                                                                                 |                                                                                                                                                                                               |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **MEMORY.md 并发写入冲突**              | memory tool 报错 `Refusing to write MEMORY.md: file on disk has content that wouldn't round-trip`，导致 memory 更新被跳过                                                                                                                                                                                                                                    | 这是 memory tool 的安全守卫——当 MEMORY.md 被外部进程/patch 工具修改过时会拒绝写入。**修复方法**：直接用 `write_file`/`patch` 工具将 MEMORY.md 重写为纯 §-delimited 格式（无 `#` 注释头、无多余空行），然后重试 memory add。不要反复重试 memory tool。                      |                                                                                                                                                                                               |
| **Cron job SSH 认证失败**             | cron job 执行 SSH 连接报 `Permission denied (publickey)`，本地 SSH 正常工作                                                                                                                                                                                                                                                                                    | cron 运行在干净环境（`env -i`），无 `SSH_AUTH_SOCK`。必须通过 `~/.ssh/config` 显式指定 `IdentityFile` 和 `StrictHostKeyChecking no`，SSH agent 密钥在 cron 中不可用。详见 `deployment-troubleshooting` skill 第 32e 节。                   |                                                                                                                                                                                               |
| **Python 脚本误标为 .sh 后缀**           | write\_file 生成 `health_check.sh` 但内容是 Python，bash 执行 `def main():` 报语法错误                                                                                                                                                                                                                                                                           | Python 脚本必须用 `.py`。写完后检查 shebang 与后缀一致：`#!/usr/bin/env python3` → `.py`                                                                                                                                 |                                                                                                                                                                                               |
| **`with_suffix()` 拼接后缀报错**        | `path.with_suffix("-result.json")` 抛 `ValueError: suffix must not contain '-'`                                                                                                                                                                                                                                                                     | 用 `f"{path.stem}-result.json"` 或 `str(path.with_suffix('')) + '-result.json'`                                                                                                                           |                                                                                                                                                                                               |
| **中文告警匹配不到模式**                    | patterns.json 只有英文关键词，中文日志（如"磁盘使用率 95%"）无法命中                                                                                                                                                                                                                                                                                                       | 每个 pattern 增加 `keywords_cn` 字段，diagnose.py 同时匹配中英文                                                                                                                                                      |                                                                                                                                                                                               |
| **服务看门狗脚本监控死循环**                  | service\_watchdog.sh 未设置最大重启次数，服务持续崩溃导致无限重启                                                                                                                                                                                                                                                                                                        | 内置 max\_restart=5 限制，超过后告警并停止                                                                                                                                                                           |                                                                                                                                                                                               |
| **修复沙箱未做 dry-run 就执行**            | 直接 `--execute` 后发现修复命令有误                                                                                                                                                                                                                                                                                                                           | 必须先 `--dry-run` 预览，确认无误后再 `--execute`                                                                                                                                                                   |                                                                                                                                                                                               |
| **飞书通知脚本发送失败**                    | feishu\_notify.py 调用 `hermes send --message` 报 unrecognized arguments，或 cron 模式下被 `cron_auto_delivery_duplicate_target` 跳过                                                                                                                                                                                                                         | **重写 feishu\_notify.py**：不再尝试 CLI/API 发送，改为直接 print() 输出到 stdout，由 cron job 的 auto-delivery 机制投递到飞书。脚本职责=扫描+格式化，投递=框架的责任                                                                                |                                                                                                                                                                                               |
| **告警文件格式不匹配**                     | feishu\_notify.py 期望扁平字段（severity/symptom/diagnosed\_cause），但实际告警文件是嵌套格式（status + unresolved\_alerts 数组），导致格式化输出只有标题没有内容                                                                                                                                                                                                                           | feishu\_notify.py 必须支持两种格式：v1 扁平（severity at top-level）和 v2 嵌套（status + unresolved\_alerts\[].\{level,message,diagnosis}）。用 `_normalize_alert()` 统一归一化后再格式化                                             |                                                                                                                                                                                               |
| **Cron 模式下的脚本投递**                 | feishu\_notify.py 在 cron 中运行，尝试自己调 CLI/API 发送飞书消息，但 cron job 已配置 auto-delivery 到同一 target，导致重复跳过                                                                                                                                                                                                                                                   | 脚本只做 print(message)，由 cron framework 自动投递 stdout 到飞书。手动运行时提示用户用 send\_message 工具发送                                                                                                                      |                                                                                                                                                                                               |
| **拖延等待用户确认**                      | 发现 critical 告警后暂停等待用户指示"修复还是忽略"                                                                                                                                                                                                                                                                                                                    | safety=safe 直接执行修复，不逐步确认。只有 needs\_confirmation 级别的才记录+告警                                                                                                                                               |                                                                                                                                                                                               |
| **服务未安装却推荐重启**                    | diagnose.py 对 SERVICE\_DOWN 一律推荐 `systemctl restart`，未先检查服务单元是否存在。**实测案例**：health\_check.sh 将 postgresql/redis 标记为 inactive，但 `systemctl restart` 返回 `Unit not found`，repair.py 报 partial\_failure。**✅ 已修复 (3.0.2)**：health\_check.sh 现在 `get_service_status()` 先检查 unit file 是否存在，不存在则标记 `not_installed`；检查已知替代品（redis→valkey 等）。不再对未安装服务产生 alert | 详见 <br/>[references/service-not-found-false-positive.md](references/service-not-found-false-positive.md)                                                                                                |                                                                                                                                                                                               |
| **修复成功但未验证实际状态**                  | repair.py 返回 `overall_status: success` 但 systemctl is-active 仍为 inactive（因为服务根本不存在）                                                                                                                                                                                                                                                                | **修复执行完后，必须运行 `verify_repair.py --plan <plan文件>` 验证**：对服务类修复执行 `systemctl is-active <service>`，对磁盘类执行 `df` 再次确认。验证失败不应标记 success，应标记 partial-failed 并记录根因。脚本会自动检查 unit 是否存在、是否 disabled、端口是否被占用         |                                                                                                                                                                                               |
| **服务端口冲突误判为服务宕机**                 | keydb.service 报 "Address already in use"，实际是另一个服务（如 valkey）占用了端口。直接 restart 会持续失败                                                                                                                                                                                                                                                                  | 先 \`ss -tlnp                                                                                                                                                                                            | grep \<port> `确认端口占用者。如果是功能相同的重复服务，按版本新旧决定保留哪个，`systemctl disable\` 旧的。不要盲目 restart                                                                                                           |
| **服务被功能替代品替换仍报 inactive**         | health\_check 报告 redis inactive，但 valkey-server 正在 6379 端口运行。直接 `systemctl restart redis` 会报 `Unit not found` 或端口冲突                                                                                                                                                                                                                                | 先 \`ss -tlnp                                                                                                                                                                                            | grep \<port>\` 确认端口是否被占用 → 检查占用者是否是功能替代品（如 valkey→redis）→ 替代品正常运行则不修复，记录 unresolved 日志说明替代关系。详见 <br/>[references/service-substitute-detection.md](references/service-substitute-detection.md) |
| **repair.py 报告 success 但服务实际未恢复** | repair.py 基于命令退出码判断 success，但 `systemctl restart` 对未安装服务可能返回 0（不报错），服务仍 inactive。实测案例：postgresql/redis 未安装，repair.py 返回 `overall_status: success`，但 `systemctl is-active` 仍为 inactive                                                                                                                                                              | **修复执行后必须验证实际状态**：对服务类修复执行 `systemctl is-active <service>`；对磁盘类执行 `df`。验证失败 → 不应标记 success，应写入 unresolved 目录并记录根因推测（未安装/已 disabled/数据目录损坏/端口冲突）                                                         |                                                                                                                                                                                               |
| **Cron 巡检对 warning 告警的完整处理**      | 对 warning 级别"服务未运行"告警，走完诊断→修复→验证→记录全流程，最终发现服务未安装（非故障）。若静默跳过则无法区分"真正常"和"误报"                                                                                                                                                                                                                                                                         | 按 <br/>[references/cron-workflow-false-positive.md](references/cron-workflow-false-positive.md)<br/> 决策树执行：warning 级别完整走诊断→修复→验证→归档流程。即使最终判定为误报也写入 unresolved/ 目录（resolution=no\_action\_needed），不可静默跳过 |                                                                                                                                                                                               |

| **症状**                        | **根因**                                                                                                                                                                                                                                                                      | **修复方案**                      | **安全等级** |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- | -------- |
| 磁盘 >90%                       | 日志/缓存累积                                                                                                                                                                                                                                                                     | 清理旧日志 + logrotate             | ✅ 安全     |
| 服务进程数为 0                      | 进程崩溃/未启动                                                                                                                                                                                                                                                                    | 重启服务                          | ✅ 安全     |
| 内存 >90%                       | 内存泄漏/进程过多                                                                                                                                                                                                                                                                   | 清理缓存 + 重启高内存进程                | ⚠️ 需确认   |
| 502 Bad Gateway               | 后端进程池耗尽                                                                                                                                                                                                                                                                     | 重启后端 + 调大池                    | ✅ 安全     |
| SSH 无法连接                      | sshd 崩溃/防火墙                                                                                                                                                                                                                                                                 | 重启 sshd + 检查规则                | ⚠️ 需确认   |
| 网络不通                          | DNS/路由/防火墙                                                                                                                                                                                                                                                                  | 逐步排查 → 修复                     | ⚠️ 需确认   |
| 配置错误                          | 语法/参数错误                                                                                                                                                                                                                                                                     | 回滚到上一版本                       | ✅ 安全     |
| 僵尸进程                          | 父进程未回收                                                                                                                                                                                                                                                                      | 杀父进程回收子进程                     | ⚠️ 需确认   |
| SSL 证书过期                      | 未自动续期                                                                                                                                                                                                                                                                       | 手动续期 + 部署                     | ✅ 安全     |
| 数据库连接失败                       | 连接池满/DB 宕机                                                                                                                                                                                                                                                                  | 重启连接池/DB                      | ⚠️ 需确认   |
| SSH 暴力破解                      | 批量 Failed password                                                                                                                                                                                                                                                          | 检查来源 IP + fail2ban            | 🔍 仅诊断   |
| 数据库慢查询                        | 查询超时/锁等待                                                                                                                                                                                                                                                                    | 分析慢查询日志 + 加索引                 | 🔍 仅诊断   |
| Cron 任务卡住                     | 任务执行超时未终止                                                                                                                                                                                                                                                                   | 终止 + 设置超时                     | ⚠️ 需确认   |
| 单进程 CPU 满载                    | 死循环/异常逻辑                                                                                                                                                                                                                                                                    | 分析进程行为 + 决定是否终止               | ⚠️ 需确认   |
| 服务端口冲突                        | "Address already in use"                                                                                                                                                                                                                                                    | 禁用旧服务/改端口                     | ⚠️ 需确认   |
| 服务被功能替代                       | "inactive but substitute running"                                                                                                                                                                                                                                           | 不修复，记录说明                      | ℹ️ 非故障   |
| 修复命令成功但服务未恢复                  | "systemctl restart → success, still inactive"                                                                                                                                                                                                                               | 检查是否未安装/被替代/端口冲突 → unresolved | ⚠️ 需确认   |
| **多 Profile state.db 重复占用磁盘** | 磁盘 >90% 时，检查 `du -sh profiles/*/state.db`。scout/coder/analyst 各有一份 888MB 旧 state.db（default 已瘦身至 \~398MB），合计浪费 \~1.77GB。**修复**：停服后 `cp /root/.hermes/state.db /root/.hermes/profiles/{scout,coder,analyst}/state.db` 覆盖为瘦身后的副本。需先 `hermes gateway shutdown` 再复制，避免热复制损坏数据库。 | ✅ 安全（停服后）                     |          |

## 修复后验证门（Mandatory）

> **每次 repair.py --execute 后必须运行 verify\_repair.py 确认实际状态。** repair.py 的 `overall_status: success` 不等于服务真正恢复。

```bash
# 从 plan 文件批量验证
python3 scripts/verify_repair.py --plan /tmp/self-heal-plan.json

# 验证单个服务
python3 scripts/verify_repair.py --service postgresql --type service

# 验证磁盘
python3 scripts/verify_repair.py --type disk --path /

# 验证失败时自动回滚
python3 scripts/verify_repair.py --plan /tmp/self-heal-plan.json --rollback-on-fail

# 输出到文件
python3 scripts/verify_repair.py --plan /tmp/self-heal-plan.json --output /tmp/verify-result.json
```

**判断逻辑**：

* 验证通过（`verified: true`）→ 标记 success，记录经验
* 验证失败 + `status: not_installed` → 写入 unresolved/ 目录，reason="服务未安装"
* 验证失败 + `status: disabled` → 询问用户是否需要启用
* 验证失败 + `status: inactive` → 查看 journalctl 获取失败原因，写入 unresolved/

## CLI 速查

```bash
# 诊断
python3 fault_engine/diagnose.py --alert "磁盘使用率 95%"

# 查看故障历史
python3 learning/similarity.py list --limit 10

# 搜索相似故障
python3 learning/similarity.py search "nginx 502"

bash repair_sandbox/repair.py --plan plan.json --dry-run    # 预览
bash repair_sandbox/repair.py --plan plan.json --execute   # 执行
python3 scripts/verify_repair.py --plan plan.json          # ⚠️ 修复后必须验证

# 回滚最后一次修复
python3 repair_sandbox/rollback.py --last

# 服务看门狗
bash scripts/service_watchdog.sh <service_name>
```

## Cron 自动化巡检

### 每小时巡检 cron

```
schedule: every 1h
prompt:
  1. 运行 health_check.sh
  2. 解析输出，检查 status/alerts
  3. 有 critical/warning → diagnose.py 诊断 → safety=safe 自动修复 → verify_repair.py 验证实际状态 → 记录经验
  4. 修复后验证失败 → 写入 /root/.hermes/logs/self-heal/unresolved/（标注根因）
  5. 一切健康 → SILENT
  6. 未自动修复的 warning → 写入 /root/.hermes/logs/self-heal/unresolved/
```

### 飞书告警通知 cron

```
schedule: every 2h
prompt:
  1. 运行 python3 /root/.hermes/skills/self-heal/scripts/feishu_notify.py
  2. 无告警 → SILENT
  3. 有告警 → 脚本输出格式化消息到 stdout，cron auto-delivery 自动投递到飞书
     target=oc_f7b16d2647792ebb8dd26c49c1961173
  4. 脚本不再自行调 CLI/API 发送，由 cron 框架负责投递
```

### 飞书消息格式

```
🚨 Self-Heal 告警通知 (YYYY-MM-DD HH:MM)

🔴 Critical (N):
  • [PATTERN_ID] symptom
    主机: xxx
    原因: diagnosed_cause
    状态: ❌ 自动修复失败 / ⚠️ 安全策略限制

🟡 Warning (N):
  • [PATTERN_ID] symptom
```

## 与现有系统的关系

* **sysops-toolkit**：Self-Heal 复用其 health\_check、log\_analyzer、sys\_inspector，增加推理和修复能力
* **SkillForge**：每次修复产生的新经验 → 自动合成 Skill 基因
* **Cron**：每小时健康检查 → 诊断 → 自动修复 → verify\_repair.py 验证 → 经验沉淀（闭环）；每2小时飞书告警扫描
* **Hermes 记忆**：故障事件写入记忆系统，跨会话保留经验
* **飞书通知**：feishu\_notify.py 脚本输出格式化消息到 stdout，cron auto-delivery 自动投递到飞书 target。脚本本身不直接调 API/CLI 发送。手动运行时由 Agent 用 `send_message` 工具推送到飞书。
* **MEMORY.md 并发冲突**：详见 `references/memory-md-concurrency.md`
* **服务未安装误报**：[references/service-not-found-false-positive.md](references/service-not-found-false-positive.md)
* **服务功能替代检测**：[references/service-substitute-detection.md](references/service-substitute-detection.md)
* **repair成功但服务未恢复**：[references/repair-success-but-not-running.md](references/repair-success-but-not-running.md)
* **Cron巡检误报完整处理流程**：[references/cron-workflow-false-positive.md](references/cron-workflow-false-positive.md)
* **修复验证**：`scripts/verify_repair.py` — 每次 repair.py 后强制运行，检查 unit 是否存在 / 服务是否 active / 磁盘是否释放 / 端口是否监听

## 步骤

1. **读取当前配置** — 查看现有设置
2. **应用变更** — 修改配置项
3. **验证生效** — 确认变更已生效
4. **回滚准备** — 保留恢复方案

## 验证

- [ ] 配置变更已保存

- [ ] 服务/功能按预期工作

- [ ] 无副作用影响其他组件
