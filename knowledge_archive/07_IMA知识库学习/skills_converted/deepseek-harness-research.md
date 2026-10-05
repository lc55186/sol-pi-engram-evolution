---
name: deepseek-harness-research
description: DeepSeek Harness 深度研究笔记
version: 1.0.0
category: research
tags: ["deepseek", "harness", "cordis", "plugin-architecture"]
metadata:
  hermes:
    tags: ["deepseek", "harness", "cordis", "plugin-architecture"]
    source: IMA 知识库导入
---

# deepseek-harness-research

> DeepSeek Harness 深度研究笔记。 DeepSeek AI 发布的开源 Agent 框架，采用"一切皆插件"架构，由 Cordis 驱动。 核心概念：Plugin、Context、Dependency Injection、Typed Events、Reversible Effects。 触发词：DeepSeek Harness / dsh / Cordis / 一切皆插件 / deepseek-agent。

# DeepSeek Harness 深度研究笔记

## 项目概况

| **维度**     | **详情**                                                                                             |
| ---------- | -------------------------------------------------------------------------------------------------- |
| **GitHub** | [https://github.com/deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) |
| **开发者**    | DeepSeek AI                                                                                        |
| **定位**     | 开源 Agent Harness（智能体框架）                                                                            |
| **架构理念**   | 一切皆插件（Everything is a Plugin）                                                                      |
| **底层驱动**   | Cordis（时空组合性元框架）                                                                                   |
| **状态**     | 开发者预览（Developer Preview），快速迭代中                                                                     |
| **许可证**    | MIT                                                                                                |
| **Web UI** | [http://127.0.0.1:3080](http://127.0.0.1:3080)                                                     |
| **论文**     | _A Programming Paradigm for Spatiotemporal Composability_                                          |

***

## 核心架构

### Cordis 五大核心理念

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Cordis 五大核心理念                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. Plugin = 实现 Service 的对象                                    │
│     ├── 函数 + inject + apply(ctx)                                  │
│     └── Service 子类，生命周期由 Cordis 管理                        │
│                                                                     │
│  2. Context = 服务的仓库                                            │
│     ├── ctx.tools, ctx.llm, ctx.sessions                           │
│     └── 通过 key 查找服务，而非 import 具体实现                     │
│                                                                     │
│  3. Dependency Injection via inject                                 │
│     ├── 声明所需服务                                                │
│     └── 加载顺序通过服务需求表达，非手动引导                        │
│                                                                     │
│  4. Typed Events 通信                                               │
│     ├── emit（广播，无返回值）                                      │
│     ├── waterfall（拦截，有返回值，可短路）                         │
│     ├── parallel（并行，等待所有监听器）                            │
│     └── serial（串行，按顺序执行）                                  │
│                                                                     │
│  5. Reversible Effects（可逆效果）                                  │
│     ├── ctx.effect() / ctx.on() 注册                               │
│     ├── reload 和 teardown 自动撤销                                │
│     └── 注册顺序即卸载顺序                                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 事件分发模式

| **模式**      | **等待？** | **执行顺序** | **有返回值？** | **用途**  |
| ----------- | ------- | -------- | --------- | ------- |
| `emit`      | 否       | 按注册顺序    | 否         | 广播通知    |
| `waterfall` | 否       | 按注册顺序    | 是         | 拦截器/中间件 |
| `parallel`  | 是       | 并行执行     | 否         | 独立任务    |
| `serial`    | 是       | 按注册顺序    | 是         | 顺序处理    |

### Waterfall 语义（中间件模式）

```typescript
// 监听器接收 (...args, next)
ctx.waterfall('tools/execute', async (toolCall, next) => {
    // 1. 预处理
    const modifiedCall = await transform(toolCall);
    
    // 2. 委托给下一个服务（可短路）
    const result = await next(modifiedCall);
    
    // 3. 后处理
    return result;
});
```

***

## 系统架构

### 分层架构（Profiles & Bundles）

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DeepSeek Harness 分层架构                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Profile（用户配置）                                                │
│  ├── cordis.patch.yml（用户自定义补丁）                             │
│  ├── 安装的 out-of-tree plugins                                    │
│  └── Bundle 列表                                                   │
│                                                                     │
│  Bundles（可复用模块包）                                            │
│  ├── dsh-base（第一层，所有 Profile 的基础）                        │
│  │   ├── model adapters（模型适配器）                              │
│  │   ├── tools（工具注册表）                                       │
│  │   ├── persistence（持久化）                                     │
│  │   ├── sandbox（沙箱）                                           │
│  │   ├── approval policy（审批策略）                               │
│  │   ├── settings（设置）                                          │
│  │   ├── credentials（凭证）                                       │
│  │   └── telemetry（遥测）                                         │
│  ├── dsh-web-app（Web UI 应用）                                    │
│  └── dsh-headless（无服务器一次性运行器）                          │
│                                           
```

## 触发条件

DeepSeek Harness 深度研究笔记。 DeepSeek AI 发布的开源 Agent 框架，采用"一切皆插件"架构，由 Cordis 驱动。 核心概念：Plugin、Context、Dependency Injection、Typed Events、Reversible Effects。 触发词：DeepSeek Harness / dsh / 
## 验证

- [ ] 按上述步骤执行成功
- [ ] 输出符合预期，无报错
