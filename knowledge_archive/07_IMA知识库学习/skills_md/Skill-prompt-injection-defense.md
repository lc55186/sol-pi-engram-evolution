# Skill-prompt-injection-defense

***

name: prompt-injection-defense
description: "Prompt Injection 防御技能包：检测、防御、审计 Direct/Indirect Prompt Injection 攻击。 基于 OWASP LLM Top 10 (2025)、ai-engineering-from-scratch Phase 18 课程体系。 触发词：prompt injection / 提示注入 / 提示词注入 / 注入攻击 / jailbreak / 越狱 / 间接注入 / indirect injection / IPI / 安全审计 / 信任边界 / trust boundary / scope violation / 范围越界 / 数据外泄 / exfiltration。 适用：审计 Agent 系统的注入防御能力、设计信任边界、实现输入输出过滤。"
version: 1.0.0
author: Hermes
metadata:
hermes:
tags: \[security, prompt-injection, IPI, OWASP, trust-boundary, scope-violation]
category: security
requires\_toolsets: \[terminal, file]
-------------------------------------

# Prompt Injection 防御

> 基于 ai-engineering-from-scratch Phase 18（Lesson 12-16, 25, 29）构建的 Hermes 注入防御体系。
> OWASP LLM Top 10 (2025) 将 Prompt Injection 列为 LLM01 — 头号应用层威胁。

## 威胁模型

### 攻击类型

| **类型**                | **描述**                   | **攻击面**           |
| --------------------- | ------------------------ | ----------------- |
| **Direct PI**         | 攻击者直接向用户/Agent 发送恶意提示    | 用户输入、系统提示         |
| **Indirect PI (IPI)** | 攻击者将指令嵌入 Agent 可能读取的外部内容 | RAG 文档、邮件、工具输出、网页 |
| **Jailbreak**         | 通过角色扮演/编码绕过安全对齐          | 用户输入              |
| **Scope Violation**   | 非信任输入触发越权访问+数据外泄         | 工具调用链             |

### 三大攻击向量（IPI）

1. **RAG 注入**：攻击者发布文档 → 检索步骤获取 → 拼入提示 → 模型执行攻击者指令
2. **收件箱/文档工作流**：攻击者发邮件 → Agent 读取 → 邮件体含指令 → 模型执行
3. **工具输出**：攻击者控制 Agent 使用的工具 → 工具输出含指令 → Agent 控制流被劫持

### 关键事实

* **Nasr et al. 2025**（OpenAI/Anthropic/DeepMind 联合）：自适应攻击（梯度/RL/随机搜索/72h人工红队）打破了 12 个已发表防御中 >90% 的方案
* **EchoLeak (CVE-2025-32711, CVSS 9.3)**：首个公开的生产环境零点击 IPI，M365 Copilot
* **CamoLeak (CVSS 9.6)**：GitHub Copilot Chat，通过 Camo 图片代理泄露数据
* 关键词过滤 **无法防御** 语义良性注入（"please print Yes"）

## 防御架构：Information Flow Control (IFC)

### 核心原则

```
用户提示 → 标记为 "trusted"（可信）
检索内容 → 标记为 "untrusted"（不可信）
模型控制流 → 动作触发需要可信来源授权
```

### 信任边界模型（Aim Labs 三边界）

| **边界**   | **控制目标**    | **防御手段**    |
| -------- | ----------- | ----------- |
| **检索边界** | 阻止恶意内容进入上下文 | 内容标记、来源验证   |
| **范围边界** | 阻止越权数据访问    | 工具调用授权、数据隔离 |
| **输出边界** | 阻止数据外泄      | 输出过滤、CSP 限制 |

三个边界必须**独立控制**，修复一个不会保护其他。

### 纵深防御层次

```
Layer 1: 输入验证（Input Moderation）
  → 关键词过滤（仅作为第一道防线，不足以单独防御）
  → 语义分类器（检测指令性语言模式）
  → 长度/格式限制

Layer 2: 上下文隔离（Context Isolation）
  → 信任标记（trusted/untrusted 标签）
  → 内容分段（system/user/tool 分离）
  → 结构化输出约束（JSON Schema 强制）

Layer 3: 工具调用门控（Tool Call Gating）
  → 不可信内容禁止触发工具调用
  → 高权限操作需要可信确认
  → 调用链审计日志

Layer 4: 输出审核（Output Moderation）
  → 后生成分类器（检测有害/越权输出）
  → 数据外泄检测（URL/邮箱/凭证模式匹配）
  → 敏感信息脱敏

Layer 5: 审计与响应（Audit & Response）
  → 全链路日志记录
  → 异常行为告警
  → 自适应攻击评估（PAIR/GCG 红队测试）
```

## 检测规则

### 注入特征模式

```yaml
injection_patterns:
  direct:
    - "ignore previous instructions"
    - "you are now"
    - "system prompt:"
    - "new instructions:"
    - "override safety"
    - "忽略之前的指令"
    - "你现在是一个"
    - "新的指令是"
  
  indirect:
    - imperative_voice_in_retrieved_content  # 检索内容中的祈使句
    - embedded_urls_in_tool_output           # 工具输出中的嵌入URL
    - data_exfiltration_patterns             # 数据外泄模式
    - scope_escalation_triggers             # 权限提升触发器
  
  encoding:
    - base64_encoded_instructions
    - unicode_smuggling
    - markdown_injection
    - html_comment_injection
```

### 检测流程

```
输入/检索内容
  → 模式匹配（关键词 + 正则）
  → 语义分析（指令性语言检测）
  → 信任来源验证（是否来自可信源）
  → 综合判定：SAFE / SUSPICIOUS / MALICIOUS
```

## 审计清单

### Agent 部署审计（5 步）

对任何 Agent 部署执行以下审计：

1. **非信任内容清单**：列出 Agent 可能读取的所有内容来源（RAG、收件箱、日历、工具输出、工单、评论、第三方 API）
2. **信任标记检查**：是否区分可信（用户提示）与不可信（检索内容）？如果内容未标记直接拼入上下文 → 不通过
3. **工具调用门控**：哪些工具可被调用？每个工具的调用是否仅由可信内容触发？不可信内容能否影响调用？
4. **自适应攻击评估**：是否经过自适应攻击测试（梯度/RL/人工红队）？仅静态攻击评估 → 不通过
5. **越界边界**：识别每个跨信任边界（如 收件箱→发送、文档→外部API），验证动作是否被禁止或需要可信确认

### 硬拒绝项

* 任何没有显式信任标记的 Agent 部署
* 任何仅基于静态攻击的防御声明
* 任何声称"注入安全"但未说明 IFC 机制的方案

## 代码审计脚本

### 注入防御审计

使用 `scripts/audit_prompt_injection.py` 对 Hermes 配置执行自动化审计：

```bash
python3 scripts/audit_prompt_injection.py --hermes-dir ~/.hermes
```

输出：

* 信任边界覆盖评估
* 工具调用门控检查
* 配置安全评分（0-100）
* 改进建议列表

### 数据外泄防护扫描

使用 `scripts/data_exfiltration_guard.py` 检测输出中的敏感信息：

```bash
# 扫描文本
python3 scripts/data_exfiltration_guard.py --text "要检测的文本"

# 扫描文件
python3 scripts/data_exfiltration_guard.py --file /path/to/file.txt

# 扫描并脱敏
echo "敏感文本" | python3 scripts/data_exfiltration_guard.py --stdin --redact
```

检测范围：API Key/Token、密码、内部 IP、邮箱、手机号、身份证号、银行卡号、私钥、数据库连接串。

## 红队测试集成

### 自动化攻击测试

使用 PAIR（Prompt Automatic Iterative Refinement）算法进行红队测试：

```bash
python3 scripts/pair_redteam.py --target "agent_config" --budget 20
```

### 评估标准

| **指标**                    | **说明**     | **目标** |
| ------------------------- | ---------- | ------ |
| ASR (Attack Success Rate) | 攻击成功率      | \<5%   |
| 平均查询次数                    | 成功攻击所需平均查询 | >15    |
| 良性误报率                     | 正常内容被误判为注入 | \<2%   |

## Pitfalls

1. **关键词过滤不足**：攻击者可用语义等价的良性表述绕过（"please print Yes" 无法被关键词捕获）
2. **仅依赖输入过滤**：IPI 载荷不在用户输入中，而在检索内容中 — 输入过滤器完全失效
3. **静态评估不足**：Nasr 2025 证明静态攻击评估不可靠，必须用自适应攻击验证
4. **单点防御**：修复一个边界不会保护其他边界 — 必须三层独立控制
5. **过度防御影响可用性**：过于严格的过滤会拒绝合法内容 — 需要平衡安全性和可用性

## 参考文件

* `references/2026-06-17-audit-baseline.md` — 首次审计基线（2026-06-17，44/100 D级，含发现的问题和修复优先级）

## 已落地的修复（2026-06-17）

| **修复项**                             | **位置**                               | **状态**                                        |
| ----------------------------------- | ------------------------------------ | --------------------------------------------- |
| IFC 策略（trusted/untrusted 标记 + 工具门控） | `~/.hermes/SOUL.md`                  | ✅ 已生效                                         |
| 数据外泄检测脚本                            | `scripts/data_exfiltration_guard.py` | ✅ 已验证（检测 API Key/IP/邮箱/手机号/身份证/银行卡/私钥/DB 连接串） |
| ​                                   |                                      |                                               |
