---
name: auto-hermes
description: Hermes 自动化核心：新 Skill 自动评估、MCP 自动审查、搜索自动增强、自主进化闭环
version: 1.0.0
category: autonomous
tags: ["automation", "auto", "evolution", "self-improvement", "closed-loop"]
metadata:
  hermes:
    tags: ["automation", "auto", "evolution", "self-improvement", "closed-loop"]
    source: IMA 知识库导入
---

# auto-hermes

> Hermes 自动化核心：新 Skill 自动评估、MCP 自动审查、搜索自动增强、自主进化闭环。 触发词：自动评估 Skill、审查 MCP、自动搜索增强、自主进化、闭环优化。 适用：持续优化 Hermes 性能、自动化质量控制、自主学习迭代。

# Auto-Hermes：Hermes 自动化核心

> **从手动到自动：** 把我们手动做的优化变成自动流程，形成闭环。

## 核心自动化流程

### 1. 新 Skill/工具/脚本 自动评估

**触发时机：** 安装/创建任何新 Skill、脚本、工具、插件、MCP Server 时（自动触发，无需手动命令）

**检查清单（6项）：**

- [ ] YAML Frontmatter（name/description/version/metadata）

- [ ] description 召回句（有触发词+场景+反例）

- [ ] When to Use（有触发场景+边界）

- [ ] Procedure（有可执行步骤+命令+判断标准）

- [ ] Verification（有三态 verdict + 下一步）

- [ ] Pitfalls（有坑→症状→Fix）

**执行流程：**

1. 读取新 Skill 的 SKILL.md
2. 用以上6项检查
3. 生成评估报告（PASS/NEEDS\_IMPROVEMENT/FAILED）
4. 自动修复可修复的问题（比如补 description）
5. 无法修复的问题，给出修复建议

### 2. MCP 自动审查

**触发时机：** 安装新 MCP 时（`hermes mcp add ...`）或手动触发 `auto-hermes audit-mcp`**审查清单（4步）：**

1. 权限范围审查（读取/写入/最坏情况/最小化）
2. 配置审查（密钥是否明文/权限宽度）
3. 运行时隔离（进程/网络/文件系统）
4. 回滚方案确认（卸载/恢复/备份）

**执行流程：**

1. 读取 MCP 配置
2. 调用审查清单（skills/security-toolkit/mcp-safety-audit/SKILL.md）
3. 生成安全报告（APPROVED/NEEDS\_RESTRICTION/REJECTED）
4. 自动限制权限（如果可能，比如域名白名单）
5. 无法限制的，给出安全建议

### 3. 搜索自动增强

**触发时机：** 每次调用 web\_search 超过 2 次，或手动触发 `auto-hermes enhance-search`**执行流程：**

1. 记录搜索结果和 Agent 反馈
2. 用 `agent-search` Skill 的查询理解模块，拆解子查询
3. 并行调用 AnySearch MCP + web\_search
4. 对比结果，找出更好的搜索词
5. 自动更新搜索词（存入 memory）

## 自主进化闭环

### 1. 纠错图谱自动记录

**触发时机：** Agent 犯错后，用户纠正（`这个不对，应该是...`）或手动触发 `auto-hermes build-error-graph`**执行流程：**

1. 读取用户纠正的内容
2. 提取错误类型、原因、修复方案
3. 存入纠错图谱（`~/.hermes/memories/error-graph.json`）
4. 下次遇到相似任务，自动从图谱中读取教训
5. 自动生成 "注意：之前你提到过，..."

### 2. 搜索效果追踪

**触发时机：** 每次搜索任务完成后，或手动触发 `auto-hermes track-search`**执行流程：**

1. 读取搜索日志（`~/.hermes/logs/tool-calls.jsonl`）
2. 对比搜索结果和 Agent 后续推理结果
3. 分析哪些搜索词/来源更有效
4. 更新 `agent-search` Skill 的查询理解逻辑
5. 自动优化后续搜索

### 3. 持续优化闭环

**执行顺序（循环）：**

```
用户任务 → Agent 执行 → 工具调用 → 结果产出 →
auto-hermes 监控 → 评估性能 → 发现优化点 →
自动修复 Skill/MCP/搜索逻辑 → 下次任务更优
```

## 自动化配置

在 `config.yaml` 中添加：

```yaml
auto_hermes:
  enabled: true
  skill_evaluation: true
  mcp_audit: true
  search_enhancement: true
  error_graph: true
  search_tracking: true
  error_rate_threshold: 0.2  # 错误率超过 20%，触发全量评估
  update_interval: 86400  # 每天自动运行一次全量优化
```

## 全量审计流程（铁律）

**触发时机**：用户说"检查所有工具"/"全量审计"/"是否全部集成"时。

**执行步骤**：

1. 扫描三个目录获取全部工具/Skill：
   * `workspace/scripts/*.py` — 工作区脚本
   * `~/.hermes/skills/*/SKILL.md` — 已安装 Skill
   * `~/.hermes/scripts/*.py` — 全局脚本
2. 对比 `workspace/TOOLS-REGISTRY.md`，找出遗漏
3. 补录遗漏工具到注册表（脚本表 + Skill 表）
4. 更新调用链和触发矩阵
5. 写入进化日志 + git commit
6. **审计标准**：100% 工具注册，0 个闲置

## 全功能验证流程（铁律）

**触发时机**：用户说"全功能正常可用"/"验证全部功能"时。

**验证清单**：

1. **Skill 可加载**：`wc -l SKILL.md` + `grep -c "Procedure\|Verification\|Pitfalls"` — 关键章节存在
2. **脚本可执行**：`python3 script.py --help` — exit 0 或包含 usage
3. **MCP 已注册**：`hermes mcp list` — 工具出现在列表中
4. **注册表已更新**：`grep -c "工具名" TOOLS-REGISTRY.md` — 每个工具都在注册表中
5. **进化日志有记录**：`grep -c "## \[2026" evolution-log.md` — 每次进化都有日志
6. **标准**：所有项通过，不接受部分完成

## ⚠️ 铁律：全部自动触发，禁止手动触发

**核心规则（2026-06-13 用户明确要求）：安装/创建任何工具、Skill、脚本、插件、MCP Server 时，自动触发学习→进化→迭代。禁止手动触发，禁止询问用户。**

* 触发条件（任一命中即自动触发）：新 Skill/脚本/工具创建或安装、现有工具发现 bug/报错/更好做法、用户纠正、发现协同机会
* 自动流程：Learn → Audit → Evolve → Verify → Log → Iterate
* 日志写入 `workspace/memory/evolution-log.md`

~~以下手动触发命令已废弃，保留仅供参考。实际使用中全部由 Agent 自动触发。~~

| **命令**                                        | **功能**         |
| --------------------------------------------- | -------------- |
| ~~`auto-hermes evaluate-skill <skill-name>`~~ | ~~评估指定 Skill~~ |
| ~~`auto-hermes audit-mcp <mcp-name>`~~        | ~~审查指定 MCP~~   |
| ~~`auto-hermes enhance-search`~~              | ~~运行搜索增强~~     |
| ~~`auto-hermes build-error-graph`~~           | ~~构建纠错图谱~~     |
| ~~`auto-hermes track-search`~~                | ~~追踪搜索效果~~     |
| ~~`auto-hermes full-cycle`~~                  | ~~执行一次完整闭环优化~~ |

## 自动融入工作流（铁律）

**核心规则（2026-06-13 用户明确要求）：所有工具/脚本/插件/Skill 完成后，自动注册到 `workspace/TOOLS-REGISTRY.md`，根据任务自动调用。不需要用户说"用一下XX"。**

* 任务进来 → 扫描 TOOLS-REGISTRY.md → 匹配触发条件 → 自动调用对应工具
* 工具之间可以链式调用（A 的输出是 B 的输入）
* 调用失败自动降级到替代方案
* 新工具安装 → 自动完成 6 步进化 → 自动注册 → 自动融入工作流

## 用户偏好

> 详见 [references/user-preferences.md](references/user-preferences.md) — 用户明确要求的自动进化/工作流集成/自动化运维/沟通风格偏好。

## 工具评估

> 详见 [references/tool-evaluation-framework.md](references/tool-evaluation-framework.md) — 新工具/项目引入时的 5 维评估框架 + 快速判定矩阵 + 历史评估记录。

## 每周冗余审计

> 源自 2026-06-28 反思：当技能数 > 100 时，控制信息带宽比持续安装更重要。

**审计机制**：`weekly-self-eviction` cron（周六 10:00）扫描调用频率，分层标记核心/观察/冗余。

核心/观察/冗余分层及合并规则，见 [references/weekly-redundancy-audit.md](references/weekly-redundancy-audit.md)。

**关键原则**：

* 观察期 ≥ 4 周，不因短期 0 调用误删
* 低频但不冗余的运维技能保留
* 连续 2 周 0 调用 + 无不可替代场景 → 考虑删除

### ⚠️ 审计闭环铁律（2026-07-11 建立）

**症状**：每周审计报告反复标记同一问题（如相同的过时 MEMORY.md 条目、相同的冗余 skill），但从未实际执行清理/合并。

**根因**：审计与执行脱节 — 报告只列问题，缺乏强制清理机制。

**规则**：当同一问题在连续 **2 次** 周度审计中被标记，第 3 次审计时**必须执行修复**，禁止再次仅做标记。

| **标记次数** | **动作**                         |
| -------- | ------------------------------ |
| 第 1 次    | 标记观察，记录到报告，下周末再评估              |
| 第 2 次    | 再次标记，确认非误判                     |
| 第 3 次起   | **强制执行**：归档/合并/删除，并从报告中移除该条目标记 |

\*_已知被标记 2 次以上但未执行的条目（2026-07-11 清算清单，本次审计后立即处理）_


