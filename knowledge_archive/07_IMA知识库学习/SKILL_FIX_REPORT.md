# 技能库质量修复 + 多模型教程核实报告（2026-10-05）

> 生成：Hermes Agent 自主维护
> 两项任务：① 54 个 IMA 导入技能描述补全 ②《Hermes 多模型无缝切换》文章命令核实
> 结果：全部落地，终检 0 异常，已提交 Git

## 一、IMA 导入技能描述补全（54 个）

### 背景
2026-10-03 从 IMA 知识库导入 54 个技能（70 个 Skill 笔记中剔除 3 空碎片 + 3 冲突）。
导入时 description 被 `first_sentence` 截断成短语（如 sysops-toolkit 只有 10 字"系统运维自动化工具包"），
召回触发词弱，`skills_list` 展示不完整。

### 修复过程（三轮）
1. **自动补全**：从正文 blockquote 提炼完整摘要 + 触发词，补全 33 个描述
2. **清洗**：补全引入 IMA 正文转义残留（`3. 0`、`config. yaml`、`CODE\_REVIEW`、混入日志行）→ 正则清洗 10 个，
   但清洗脚本把 6 个描述截得过狠（只剩"触发词"或误含日志行）
3. **手写修复**：对 6 个损坏最重的技能（flutter-core / deepseek-harness-research / hermes-auto-maintenance /
   idle-conservation-workflow / mcp-troubleshooting / session-maintenance）逐一手写高质量描述

### 效果示例
| 技能 | 旧描述 | 新描述 |
|------|--------|--------|
| sysops-toolkit | 系统运维自动化工具包（10字） | 完整功能清单 + 8 个触发场景（106字） |
| security-toolkit | 网络安全工具包（7字） | 加固/审计/入侵检测/漏洞扫描 + 触发词（110字） |
| hermes-dreaming | Hermes 梦境系统（Dreaming Engine） | 三维度梦境机制完整说明（126字） |

**终检**：54 个技能 0 个残留异常（无反斜杠转义、无日志行混入、无"只剩触发词"）。

## 二、《Hermes 多模型无缝切换》文章核实

> 来源：头条「智能合约开发」2026-09-29（wkbrowser 分享链接）
> 方法：文章每条 CLI 命令逐一在本机实测（Hermes v0.21.x / Windows）

### 核实结果（重要：外部教程的命令不可直接照抄）

| 文章写法 | 本机实测 | 结论 |
|----------|----------|------|
| `hermes model list` | ✗ `unrecognized arguments: list` | 记岔了 |
| `hermes model set provider-a/模型名` | ✗ 无 set 子命令 | 记岔了 |
| `hermes model --provider <p> <模型>` 会话内切 | ⚠️ 实际是启动级参数（`hermes -m --provider`），非热切 | 语义不同 |
| 改 `config.yaml` 切模型 | 真实入口 `hermes config set model.*`（config.yaml 有 agent 写保护） | 入口不同 |
| 多 provider 声明在 `providers:` 段、密钥走 `key_env` | ✅ 可信 | 与本机配置一致 |

**`hermes model` 实际是交互式 provider/模型选择器**（走 Nous Portal OAuth），不带子命令。

### 文章 vs 本机现状对照
文章的"手动多模型切换"理念，本机已用更优的自动化实现：
- **7 层自动 failover 链**：Agnes 国内 3 层（flash 线）+ Nous 4 层跨供应商，`model_failover.py` 自动切/自动切回
- **no-agent cron 每日巡检**（`model_daily_check.sh` 07:00）：静默纪律，异常才上报
- 文章讲"手动 `hermes model` 切"，本机**不依赖手敲**——主力挂了自动降级，恢复自动切回

文章真正有价值的部分是**成本理念**（按任务难度分级、默认便宜模型按需升级、提示缓存省 token），
已内化进 `model-redundancy-failover` 技能；命令层面的错误已记录防止误信。

### 沉淀
`model-redundancy-failover` 技能新增「外部教程命令核实」章节（3 条命令核实表 + 正确本机切换路径）。

## 三、Git 提交记录
- `5968183` V0.5 扇出落图模块 + OSINT 报告 + IMA 自学资产（前次）
- `fix` 54 个 IMA 导入技能描述补全 + model-redundancy-failover 核实章节（本次）
- `chore` 移除误提交的 tests/graph.db、logs/，补 .gitignore

## 四、方法学沉淀（可复用）
1. **外部教程/文章只当线索，不当事实**——命令逐条实测再落地（本次 4 条命令 3 条记岔）
2. **批量修描述要终检**——自动补全会引入源文转义残留，必须"补全→清洗→手写→终检"四步
3. **git add -A 会误带临时产物**（测试 db、日志），提交前查 `git show --stat`
