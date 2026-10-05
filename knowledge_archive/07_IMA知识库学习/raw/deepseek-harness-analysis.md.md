# DeepSeek Harness 深度分析报告

> 调研时间: 2026-08-14
> 数据来源: 新闻报道 + GitHub 实测
> 状态: Developer Preview (快速迭代中)

---

## 一、核心数据

| 指标 | 数值 | 说明 |
|------|------|------|
| **Stars** | 64,000+ | 上线 15 小时达成 |
| **Forks** | 5,000+ | 增速远超多数爆款项目 |
| **License** | MIT | 完全开源 |
| **语言** | TypeScript | Node.js 生态 |
| **定位** | Developer Preview | 快速迭代，兼容性不保证 |

---

## 二、核心理念：Everything is a Plugin

### 2.1 架构全景

```
DeepSeek Harness = Cordis 内核 + 插件矩阵

Cordis 内核:
  ├── 插件加载/卸载
  ├── 依赖关系管理
  ├── 效果跟踪与回滚
  └── 上下文类型系统

插件矩阵:
  ├── 模型层: DeepSeek / 其他 LLM (可换)
  ├── 工具层: Shell / Web / File / LSP (可换)
  ├── 技能层: 注册表 + 目录加载 (可换)
  ├── 会话层: 持久化 + 事件流 (可换)
  ├── 沙箱层: E2B / 本地 (可换)
  ├── 存储层: SQLite / 远程 (可换)
  ├── 调度层: Cron / 工作流 (可换)
  └── UI 层: Web / Headless / CLI (可换)
```

**关键洞察**: 没有任何部分是连在上面的固定能力。不顺眼就换。

### 2.2 两种运行模式

| 模式 | 用途 | 能力 |
|------|------|------|
| **标准模式** | 编码 Agent | 文件编辑、Shell、网页检索、计划、子代理、工作流 |
| **极简模式** | 跑基准测试 | 只留 Bash + 文件编辑器 |

极简模式说明官方对"可替换性"的自信——核心可以精简到只剩两个工具。

---

## 三、杀手级特性：Trajectory 视图

### 3.1 全程留痕

```
Agent 运行过程中的每一步:
  ├── 系统提示词注入
  ├── 思维链推理
  ├── 工具调用请求
  ├── 子 Agent 调度
  ├── 上下文注入
  └── 最终响应
      ↓
  全部写入只追加的事件日志
      ↓
  Trajectory 视图可按来源翻看
      ↓
  恢复、分叉、回放共用同一份事件流
```

### 3.2 解决的核心痛点

| 痛点 | DeepSeek 方案 |
|------|--------------|
| Token 账单不透明 | 每次上下文注入都有记录，可按来源审计 |
| 决策过程黑盒 | 思维链和工具调用全程留痕 |
| 出错无法复现 | 事件流回放 |
| 会话无法恢复 | 从任意分叉点恢复 |
| 调试困难 | 按来源过滤查看 |

**关键洞察**: "被 Claude Code 的 token 账单折磨过的人，看到这儿估计会心一笑。"

---

## 四、生态路线：Vim 式哲学

### 4.1 Vim 式设计

| Vim | DeepSeek Harness |
|-----|-----------------|
| 核心精简（编辑器） | Cordis 内核（只负责插件） |
| 生态繁荣（插件市场） | 插件矩阵（一切可换） |
| 用户自定义配置 | Profile + Patch 层 |
| `.vimrc` 共享 | 配置即代码 |
| 模式切换（Normal/Insert） | Profile 切换（web/headless） |

### 4.2 DeepSeek 的生态策略

> "DeepSeek 这半年想明白了一件事：生态比单品值钱。"

- **MIT 开源** — 吸引开发者贡献插件
- **纯插件架构** — 降低插件开发门槛
- **Developer Preview** — 坦诚不成熟，邀请共建
- **论文背书** — Cordis 时空可组合性提供理论支撑

---

## 五、与 Hermes 深度对比

### 5.1 架构差异

| 维度 | Hermes | DeepSeek Harness |
|------|--------|-----------------|
| **核心** | 8206 行 run_agent.py | Cordis 内核（极简） |
| **扩展** | Skills (Markdown) | TypeScript 插件 |
| **可替换性** | 部分（Skills 可装卸） | **完全**（连核心都可换） |
| **配置** | config.yaml | Profile + Bundle + Patch 三层 |
| **审计** | Session Search | Trajectory 视图（全程留痕） |
| **协议** | 闭源 + 部分开源 | MIT 完全开源 |
| **Stars** | 224K | 64K (15小时) |
| **成熟度** | 生产就绪 | Developer Preview |

### 5.2 关键差异分析

**Hermes 的优势:**
- 生产就绪，15 Skills 系统成熟
- 多平台支持（Telegram, Discord, Slack 等）
- 丰富的生态（97 Skills, 36 Cron）
- 长期验证（224K stars）

**DeepSeek 的优势:**
- 纯插件架构，完全可替换
- Trajectory 全程审计
- MIT 开源，无黑盒
- Vim 式生态，长期更灵活
- 时空可组合性论文支撑

### 5.3 反思与借鉴

> 我之前已经实现了 4 项 DSH 灵感设计（`dsh_inspired_architecture.py`），但这次新闻报道暴露了一个遗漏：**审计和回放**。

**需要补充的设计:**

1. **事件流日志** — 每次 Agent 操作写入只追加日志
2. **按来源过滤** — 可按 系统提示词/思维链/工具调用/子Agent 分类查看
3. **会话恢复** — 从任意分叉点恢复
4. **配置对比** — 类似 Trajectory 的 Profile/Patch 变更追踪

---

## 6. 行动建议

### 6.1 短期（本周）

1. **补充审计层** — 在 `dsh_inspired_architecture.py` 中加入 EventSourcing
2. **Profile 完善** — 创建 `developer` Profile（带 Trajectory 模式）
3. **知识沉淀** — 将 DSH 分析写入知识库

### 6.2 中期（1个月）

1. **插件接口标准化** — 定义 Skill 的 TypeScript 接口（兼容 DSH 和 Hermes）
2. **配置文件迁移** — 现有 Profile 格式兼容 DSH 的 cordis.patch.yml
3. **社区关注** — 跟踪 DSH 插件市场启动

### 6.3 长期

1. **可能迁移** — 如果 DSH 生态成熟，评估是否切换
2. **能力借鉴** — 将 Trajectory 理念融入 Hermes 增强层
3. **论文研究** — 深入 Cordis 时空可组合性理论

---

## 7. 关键引用

> "生态比单品值钱"

> "闭源 Agent 靠黑盒和锁账单堆出来的墙，被它一条一条摆到了台面上"

> "6 万星换不来一夜成熟的生态"

> "现在别拿它当生产工具，这更像一份路线宣言"

---

> 报告人: Hermes Agent 自主学习系统
> 存储位置: ~/.hermes/state/deepseek-harness-analysis.md
