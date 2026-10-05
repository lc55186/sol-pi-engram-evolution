# Skill-security-toolkit-Part1

***

name: security-toolkit
version: 1.3.0
description: 网络安全工具包。集成安全加固、安全审计、入侵检测规则、漏洞扫描、应急响应、云原生安全、自进化机制等安全脚本和知识库。当用户需要安全加固、安全审计、渗透测试、应急响应、漏洞扫描、K8s安全、决策日志、A/B测试时使用。
category: security
tags: \[安全, 加固, 审计, 渗透, 漏洞, 入侵检测, 应急, Linux安全, K8s安全, 云原生安全, 自进化, 决策日志]
-----------------------------------------------------------------------

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
