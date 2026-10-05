---
name: security-toolkit
description: 网络安全工具包
version: 1.0.0
category: security
tags: ["安全", "加固", "审计", "渗透", "漏洞", "入侵检测"]
metadata:
  hermes:
    tags: ["安全", "加固", "审计", "渗透", "漏洞", "入侵检测"]
    source: IMA 知识库导入
---

# security-toolkit

> 网络安全工具包。集成安全加固、安全审计、入侵检测规则、漏洞扫描、应急响应、云原生安全、自进化机制等安全脚本和知识库。当用户需要安全加固、安全审计、渗透测试、应急响应、漏洞扫描、K8s安全、决策日志、A/B测试时使用。

# 网络安全工具包

## 快速命令

### 安全加固 v2.0

```bash
# 预览加固影响（推荐先跑）
bash scripts/security_harden.sh --dry-run

# 执行加固
sudo bash scripts/security_harden.sh

# 跳过 SSH 加固（避免断开连接）
sudo bash scripts/security_harden.sh --skip-ssh

# 跳过防火墙（已有自定义防火墙规则时）
sudo bash scripts/security_harden.sh --skip-firewall
```

### 安全加固 v2.0 设计要点

**执行顺序**：防火墙 → SSH → Fail2ban → 内核参数 → 文件权限 → 服务清理 → 自动更新 → Auditd

**5 个关键风险修复**：

1. **SSH 端口变更顺序**：先配防火墙允许新端口 → 再改 sshd\_config → 端口变更默认 deferred（需手动确认）
2. **ip\_forward 对 K8s 的影响**：自动检测 K8s 节点（kubectl get nodes），K8s 节点保留 ip\_forward=1
3. **passwd SUID**：保留 /usr/bin/passwd SUID（普通用户改密码需要），不自动移除
4. **ICMP 允许**：防火墙允许 ICMP（ping 诊断），不再完全禁止
5. **AllowTcpForwarding**：不再强制禁止（运维需要 SSH 隧道）

**版本控制快照**：

* 所有修改前自动备份到 scripts/.snapshots/\{name}\_\{timestamp}.bak
* 保留 30 天，每月清理
* 回滚：cp .snapshots/sshd\_config\_\*.bak /etc/ssh/sshd\_config

**决策日志**：

* 所有安全相关决策记录到 scripts/.decision\_log
* 格式: \[时间] TASK:任务 | CHOICE:选择 | REASON:理由 | RESULT:结果

### 安全审计

```bash
# 系统安全审计
sudo bash scripts/security_audit.sh

# Kubernetes 安全审计
bash scripts/k8s_security_audit.sh
bash scripts/k8s_security_audit.sh --namespace production
bash scripts/k8s_security_audit.sh --json

# CI/CD 供应链安全审计
bash scripts/scan-cicd.sh <repo-path>
```

### CI/CD 供应链安全

* [CI/CD 供应链攻击分析](references/cicd-supply-chain-attack-analysis.md) — Cordyceps 类漏洞基础检测/缓解
* [CI/CD 安全审计完整流程](references/cicd-security-audit.md) — 4步审计流程 + 加固模板 + 快速扫描脚本

### 自进化机制

```bash
# 语义稳定性验证（记忆压缩前后核心查询命中检查）
bash scripts/semantic_stability_check.sh

# A/B 测试框架（对比策略效果）
bash scripts/ab_test_runner.sh "test_name" "cmd_a" "cmd_b"
```

* 安全编排与自动化响应 (SOAR) — 事件→动作映射引擎，含合规审计
* [安全运维自动化平台](references/security_ops_platform.md) — Ansible+Docker+Prometheus+Wazuh 整合架构
* [Shell 编排引擎模式](references/shell_orchestrator_pattern.md) — Bash 统一 CLI 编排（case 路由 + 关联数组状态追踪 + set -e 安全处理 + 大文件截断 + 风险评分）
* [安全加固 v2.0](references/security_harden_v2_patterns.md) — 执行顺序/风险修复/快照/决策日志
* [自进化模式](references/self-evolution-patterns.md) — 决策日志/版本快照/语义验证/A/B测试/权限分级
* [云原生安全](knowledge/KNOWLEDGE_cloud_native_security.md) — K8s PSS/NetworkPolicy/RBAC/镜像安全/密钥管理/审计
* [CI/CD 供应链攻击分析](references/cicd-supply-chain-attack-analysis.md) — Cordyceps 类漏洞检测/缓解/影响范围评估
* [安全决策日志](references/decision-log-2026-07-19.md) — AS封禁+蜜罐部署决策树、合法/非法判定标准、用户不满应对策略

## 模板库

* `templates/terraform-vpc/` — VPC Module 完整模板
* `templates/terraform-webapp/` — Web 应用基础设施模板
* `templates/ansible-nginx/` — Nginx Role 模板
* `templates/ansible-docker/` — Docker+Compose Role 模板

## 安全编排与自动化响应 (SOAR)

当安全事件（暴力破解、恶意软件、容器逃逸、提权）触发时，自动执行运维响应：

```python
# 核心模式: 事件 → 动作映射表 → 自动执行
ResponseEngine:
    BRUTE_FORCE       → [BLOCK_IP, SEND_ALERT]
    MALWARE_DETECTED  → [ISOLATE_CONTAINER, SNAPSHOT_QUARANTINE, SEND_ALERT]
    CONTAINER_ESCAPE  → [ISOLATE_CONTAINER, KILL_PROCESS, SEND_ALERT]
    PRIVILEGE_ESCALATION → [KILL_PROCESS, ISOLATE_CONTAINER, SEND_ALERT]

# 响应动作:
isolate_container(name)  → docker network disconnect bridge <name>
block_ip(ip)             → iptables -A INPUT -s <ip> -j DROP
kill_process(pid)        → os.kill(pid, 9)
snapshot_quarantine()    → 快照保存到 quarantine/<timestamp>/
send_alert(event)        → 写入 alerts.json + 日志
```

**完整实现参考**: `references/soar_orchestrator.md`

### Bash 安全脚本：grep -c 在 set -e 下静默终止

`grep -c "pattern"` 在无匹配时返回 exit code 1，`set -euo pipefail` 下脚本静默退出，无错误输出。

**影响范围**: 安全检测脚本中"统计失败次数"类逻辑（SSH暴力破解计数、恶意IP检测等）。

**修复方案 A**（pipe 模式，兼容所有场景）: 用 `grep ... | wc -l` 替代 `grep -c`。

```bash
# ❌ 静默终止（双行输出 + exit 1）
ssh_fail=$(grep -c "Failed password" /var/log/secure 2>/dev/null || echo 0)

# ✅ 正确（wc -l 总是 exit 0，单行输出）
ssh_fail=$(grep "Failed password" /var/log/secure 2>/dev/null | wc -l)
```

**修复方案 B**（`|| var=0` 模式，更简洁，适用于 `local` 赋值）:

```bash
# ❌ 错误：`|| echo 0` 产生双行输出 "0\n0"，导致算术表达式语法错误
ssh_root=$(grep -ci "PermitRootLogin yes" /etc/ssh/sshd_config 2>/dev/null || echo 0)

# ✅ 正确：`|| var=0` 在子命令失败时设置默认值
ssh_root=$(grep -ci "PermitRootLogin yes" /etc/ssh/sshd_config 2>/dev/null) || ssh_root=0
```

**根因详解**: `grep -ci` 在无匹配时，命令本身输出 `0` 并以 exit 1 退出。`|| echo 0` 又输出第二个 `0`。`$()` 捕获的是 `"0\n0"`。后续 `$(( ssh_root * 20 ))` 报 "表达式语法错误"。

**选择建议**:

* 方案 A 适合非 `local` 场景（如直接 `echo`）
* 方案 B 适合 `local var=$(cmd)` 场景（更简洁，不影响 `$()` 捕获）

### jq 安全构建 JSON（避免 shell 拼接）

安全脚本输出 JSON 报告时，用 `jq` 而非 shell 字符串拼接：

```bash
jq -n --arg ts "$(date -Iseconds)" --argjson score "$score" \
  --argjson data "$RAW_JSON" \
  '{generated_at:$ts,security_score:$score,system_health:$data}' > report.json
```

**注意**: `--argjson` 要求输入必须是合法 JSON；不确定格式时用 `--arg`（字符串化）。

### SOAR 平台设计要点

1. **事件数据库**: SQLite 存储所有安全事件 + 响应日志（可追溯）
2. **事件→动作映射**: 每种事件类型对应一组自动化动作，按序执行
3. **模拟测试**: 事件模拟器生成各类预置事件，验证响应链路
4. **合规审计**: CIS Benchmark 自动检查 + 报告（Docker/SSH 配置）
5. **闭环验证**: 所有动作结果记录到 response\_log，可审计

## 防御性操作

### 混合请求处理原则

当用户请求同时包含合法防御和非法操作时：

1. \*\*识别

---

## 补充材料

# 网络安全工具包

## 快速命令

### 安全加固 v2.0

```bash
# 预览加固影响（推荐先跑）
bash scripts/security_harden.sh --dry-run

# 执行加固
sudo bash scripts/security_harden.sh

# 跳过 SSH 加固（避免断开连接）
sudo bash scripts/security_harden.sh --skip-ssh

# 跳过防火墙（已有自定义防火墙规则时）
sudo bash scripts/security_harden.sh --skip-firewall
```

### 安全加固 v2.0 设计要点

**执行顺序**：防火墙 → SSH → Fail2ban → 内核参数 → 文件权限 → 服务清理 → 自动更新 → Auditd

**5 个关键风险修复**：

1. **SSH 端口变更顺序**：先配防火墙允许新端口 → 再改 sshd\_config → 端口变更默认 deferred（需手动确认）
2. **ip\_forward 对 K8s 的影响**：自动检测 K8s 节点（kubectl get nodes），K8s 节点保留 ip\_forward=1
3. **passwd SUID**：保留 /usr/bin/passwd SUID（普通用户改密码需要），不自动移除
4. **ICMP 允许**：防火墙允许 ICMP（ping 诊断），不再完全禁止
5. **AllowTcpForwarding**：不再强制禁止（运维需要 SSH 隧道）

**版本控制快照**：

* 所有修改前自动备份到 scripts/.snapshots/\{name}\_\{timestamp}.bak
* 保留 30 天，每月清理
* 回滚：cp .snapshots/sshd\_config\_\*.bak /etc/ssh/sshd\_config

**决策日志**：

* 所有安全相关决策记录到 scripts/.decision\_log
* 格式: \[时间] TASK:任务 | CHOICE:选择 | REASON:理由 | RESULT:结果

### 安全审计

```bash
# 系统安全审计
sudo bash scripts/security_audit.sh

# Kubernetes 安全审计
bash scripts/k8s_security_audit.sh
bash scripts/k8s_security_audit.sh --namespace production
bash scripts/k8s_security_audit.sh --json

# CI/CD 供应链安全审计
bash scripts/scan-cicd.sh <repo-path>
```

### CI/CD 供应链安全

* [CI/CD 供应链攻击分析](references/cicd-supply-chain-attack-analysis.md) — Cordyceps 类漏洞基础检测/缓解
* [CI/CD 安全审计完整流程](references/cicd-security-audit.md) — 4步审计流程 + 加固模板 + 快速扫描脚本

### 自进化机制

```bash
# 语义稳定性验证（记忆压缩前后核心查询命中检查）
bash scripts/semantic_stability_check.sh

# A/B 测试框架（对比策略效果）
bash scripts/ab_test_runner.sh "test_name" "cmd_a" "cmd_b"
```

* 安全编排与自动化响应 (SOAR) — 事件→动作映射引擎，含合规审计
* [安全运维自动化平台](references/security_ops_platform.md) — Ansible+Docker+Prometheus+Wazuh 整合架构
* [Shell 编排引擎模式](references/shell_orchestrator_pattern.md) — Bash 统一 CLI 编排（case 路由 + 关联数组状态追踪 + set -e 安全处理 + 大文件截断 + 风险评分）
* [安全加固 v2.0](references/security_harden_v2_patterns.md) — 执行顺序/风险修复/快照/决策日志
* [自进化模式](references/self-evolution-patterns.md) — 决策日志/版本快照/语义验证/A/B测试/权限分级
* [云原生安全](knowledge/KNOWLEDGE_cloud_native_security.md) — K8s PSS/NetworkPolicy/RBAC/镜像安全/密钥管理/审计
* [CI/CD 供应链攻击分析](references/cicd-supply-chain-attack-analysis.md) — Cordyceps 类漏洞检测/缓解/影响范围评估
* [安全决策日志](references/decision-log-2026-07-19.md) — AS封禁+蜜罐部署决策树、合法/非法判定标准、用户不满应对策略

## 模板库

* `templates/terraform-vpc/` — VPC Module 完整模板
* `templates/terraform-webapp/` — Web 应用基础设施模板
* `templates/ansible-nginx/` — Nginx Role 模板
* `templates/ansible-docker/` — Docker+Compose Role 模板

## 安全编排与自动化响应 (SOAR)

当安全事件（暴力破解、恶意软件、容器逃逸、提权）触发时，自动执行运维响应：

```python
# 核心模式: 事件 → 动作映射表 → 自动执行
ResponseEngine:
    BRUTE_FORCE       → [BLOCK_IP, SEND_ALERT]
    MALWARE_DETECTED  → [ISOLATE_CONTAINER, SNAPSHOT_QUARANTINE, SEND_ALERT]
    CONTAINER_ESCAPE  → [ISOLATE_CONTAINER, KI
```


