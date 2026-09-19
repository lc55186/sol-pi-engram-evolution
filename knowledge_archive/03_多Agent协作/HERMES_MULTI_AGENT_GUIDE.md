## Hermes Agent 多Agent配置 — 完整详解与差距分析

> 来源：用户分享的多Agent配置详解（2026-09）

---

### 核心架构

Hermes 多Agent体系分为**两大核心** + **5种原生协作机制**：

```
┌─────────────────────────────────────────────────────────────────┐
│                   Hermes 多Agent 体系                            │
├─────────────────────────┬───────────────────────────────────────┤
│   Profile 隔离式        │   会话内/跨进程协作式                   │
│   · 独立 config.yaml    │   · delegate_task 并行子Agent          │
│   · 独立 .env 密钥      │   · Kanban 持久化看板                  │
│   · 独立记忆/会话/技能   │   · Mixture of Agents 多模型投票       │
│   · 独立网关端口        │   · send_message 跨Profile通信         │
│                         │   · Background Review 空闲自动优化     │
└─────────────────────────┴───────────────────────────────────────┘
```

---

### 一、Profile 多实例隔离（最常用）

**核心原理**：`HERMES_HOME` 环境变量划分数据目录

| 路径 | 用途 |
|------|------|
| `~/.hermes/` | 默认主 Agent |
| `~/.hermes/profiles/<name>/` | 自定义 Profile |

**基础命令**：

```bash
# 创建空白 Profile（专职研究员）
hermes profile create researcher --description "财报分析、行业调研"

# 克隆现有配置（复用模型、密钥、人设，全新记忆）
hermes profile create coder --clone

# 完整克隆（配置+记忆+技能，用于备份）
hermes profile create coder-backup --clone-from coder --clone-all

# 切换默认 Agent
hermes profile use coder

# 查看所有 Agent 实例状态
hermes profile list

# 单独操作指定 Agent
coder chat
researcher gateway start
hermes -p researcher config set model.default anthropic/claude-sonnet-4
```

**Profile 独立配置项**：

```yaml
# 编码 Agent 专属配置
model:
  default: deepseek-coder-v2

delegation:
  max_concurrent_children: 2

terminal:
  cwd: /home/projects/code    # 专属工作目录
  home_mode: profile          # 独立隔离终端环境

toolsets: [file, terminal, git]  # 仅开放编码相关工具

gateway:
  port: 8643                  # 独立端口
```

**资源共享策略**：

| 模式 | 记忆 | 技能 | 会话 | 适用场景 |
|------|------|------|------|---------|
| 完全隔离（默认） | 独立 | 独立 | 独立 | 生产多角色 Agent |
| 共享技能 | 独立 | 全局共享 | 独立 | 统一工具库，个性化人设 |
| 共享记忆+技能 | 全局共享 | 全局共享 | 独立 | 团队协作统一知识库 |

**禁忌**：禁止多个进程挂载同一个 Profile 目录，会导致记忆互相覆盖。

---

### 二、delegate_task 并行子Agent

**配置参数**：

```yaml
delegation:
  max_spawn_depth: 1           # 默认扁平委派，设为2可嵌套
  max_concurrent_children: 3   # 最大并行子Agent数量
  max_iterations: 50           # 单个子Agent最大迭代步数
  orchestrator_enabled: true   # 允许子Agent继续委派
```

**角色定义**：

| 角色 | 说明 | 适用场景 |
|------|------|---------|
| `leaf`（默认） | Worker，禁止二次委派 | 95% 任务 |
| `orchestrator` | 调度角色，可派生二级子Agent | 复杂流水线 |

**权限隔离规则**：
- 子Agent 工具集 = 父Agent可用工具集 ∩ 指定工具集 - 委派黑名单
- 子Agent **不继承**父会话历史、上下文文件
- 所有上下文必须写入 goal 描述

---

### 三、Kanban 持久化看板

**特点**：跨重启、跨Profile、SQLite 存储、DAG 流水线

```bash
hermes kanban init                              # 初始化数据库
hermes kanban boards create project-x --name "项目X"  # 创建看板
hermes kanban create "后端接口开发" --assignee coder --board project-x
hermes kanban dispatch                          # 启动调度器
```

**配置**：

```yaml
kanban:
  auto_decompose: true   # 自动拆解大任务为子任务
  max_spawn: 4           # 最大同时运行的Worker进程数
  task_ttl: 3600         # 任务超时自动回收
  max_retries: 2         # 任务失败重试次数
```

**调度逻辑**：Dispatcher 每60秒轮询：回收过期→就绪任务分配给对应Profile Worker→独立子进程执行→自动更新状态。

---

### 四、其余原生协作机制

| 机制 | 用途 | 配置 |
|------|------|------|
| Mixture of Agents | 多模型投票聚合（4轻量+1聚合） | 指定多模型列表 |
| send_message | 跨Profile同网关消息通信 | 依赖IM频道中转 |
| Background Review | 空闲时自动提炼记忆优化技能 | 默认开启 |

---

### 五、Issue → PR 流水线（核心洞察）

**文章最重要的观点**：Hermes 是"项目经理+调度系统"，不是"第四个程序员"

```
GitHub Issue
    ↓
① Researcher（不改代码）→ research.md
    ↓
② Designer（方案设计）→ design.md
    ↓
③ Implementer（执行变更）→ 代码diff + 测试结果
    ↓
④ Reviewer（不改代码）→ review.md
    ↓
人工确认 → GitHub PR
```

**关键原则**：
- 研究员不写码，写代码不做评审（职责分离）
- 失败 → 阻塞等待，不盲目重试
- 人工卡在最后一步（PR前确认）
- 每个Agent只读上一阶段的产物，可恢复

---

### 六、当前系统差距分析

| 模块 | 当前状态 | 文章推荐 | 改进方案 |
|------|---------|---------|---------|
| Profile 隔离 | ✅ researcher + deployer | 独立config/记忆/技能/网关 | 完全达标 |
| delegate_task | ⚠️ 未显式配置 | max_concurrent_children=3 | 当前 max_iterations=250，需确认并发数 |
| Kanban | ❌ 未启用 | 跨重启/持久化多Agent | `hermes kanban init` 即可启用 |
| Background Review | ❌ 未配置 | 空闲时自动提炼记忆 | 默认应已启用 |
| Mixture of Agents | ⚠️ 已配置MOA | 多模型投票聚合 | 当前MOA已启用（4 reference models） |
| send_message | ✅ 间接通过飞书 | 跨Profile消息通信 | 已有 Bot Bridge 替代 |
| Docker Compose | ❌ Docker未安装 | 批量部署多Agent fleet | 暂不可用 |

---

### 七、改进建议（按优先级）

**P0（立即可做）**：

1. **启用 Kanban** — `hermes kanban init` + `hermes kanban dispatch`
   - Bot Bridge 的轮询调度可迁移到 Kanban 原生方案
   
2. **确认 delegate_task 并发数** — 检查当前 max_concurrent_children
   - 3路并行已满足大多数场景

**P1（本周内）**：

3. **完善 Profile 分工** — 增加 Designer 和 Reviewer 角色
   - Researcher = 研究+调研（已存在）
   - Deployer = 执行+部署（已存在）
   - Designer = 方案设计（可创建或复用 Claude Code profile）
   - Reviewer = 代码评审（可创建独立 profile）

4. **实现 Issue→PR 自动化** — GitHub MCP + delegate_task + Kanban 组合

**P2（持续）**：

5. **Docker 部署** — 后续安装 Docker 后可一键部署多 Agent fleet
6. **成本优化** — 子Agent用轻量模型，汇总决策用大模型

---

### 八、总结

**核心认知升级**：

1. 满配不是"装满"，而是"可长期维护、可持续进化"
2. Hermes 的价值是"把执行能力组织起来"，不是再造一个 Claude Code
3. 研究员不写码，写代码不做评审（职责分离）
4. 失败 → 阻塞等待，不盲目重试
5. 人工卡在最后一步（PR前确认）
6. 每个阶段的产物是"可交接的结果"，Agent 中途退出也可恢复

---

*文档保存时间：2026-09-19*
