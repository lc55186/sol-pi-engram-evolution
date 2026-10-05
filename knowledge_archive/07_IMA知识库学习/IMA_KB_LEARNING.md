# IMA 知识库自主学习报告

> 生成时间：2026-10-03
> 数据来源：IMA OpenAPI 真实调用（无 mock）
> 学习范围：66 个知识库 → 678 条检索命中 → 96 篇笔记 + 20 篇原文下载

## 一、权限模型（关键发现）

| 库类型 | 数量 | 搜索 | 读原文 |
|--------|------|------|--------|
| 我加入的订阅知识库 | 61 | ✅ | ❌ `code=220030 没有权限通过skill获取订阅知识库的文件` |
| 共享知识库 | 2 | ✅ | ✅ |
| 个人知识库 | 2 | ✅ | ✅ |

**结论**：订阅库只能搜标题（可作知识索引），**共享库/个人库可读全文**。
`无妄生欢的知识库`（个人库）含 **70 个 Skill 笔记（media_type=11）**，全部可读——这是本次最大收获。

## 二、检索方法学（实测验证）

- **单关键词命中率远高于多词复合**：「记忆」85 条 vs「Agent 记忆 架构」3 条；「RAG」100 条 vs「RAG 检索增强 最佳实践」0 条
- 原因：IMA 搜索按标题匹配，复合词要求全词命中
- **对策**：先单关键词广搜，再在结果里筛标题

## 三、核心知识提炼

### 3.1 Hermes 自我进化体系 v2.0（来自 `Skill-self-evolution`）

完整体系含 **15 个子系统**，分三个进化层次：

| 层次 | 工具 | 作用对象 |
|------|------|---------|
| Skill 质量 | `darwin-skill`（9 维 rubric + 爬山优化 + git 版本控制） | SKILL.md 本身 |
| 任务产出 | `adversarial-evaluator`（Generator-Evaluator 分离 + 独立上下文） | 生成器输出 |
| Skill 效用 | `skill_utility_tracker`（EMA 分数 + 衰减） | 每次使用后自动 |
| Harness | `self-harness`（失败收集→缺陷分类→回归测试→周报） | SOUL.md/Skill/提示词 |

其他关键子系统：
- **`learning-engine`**：7 步学习闭环（SOUL初始化→路径规划→深度拆解→测试回忆→应用转化→自我进化→循环）。实测 4主题×6模块×30天并行，~15 分钟生成 20 个文件
- **`skillopt-integrator`**（微软开源 arXiv 2605.23904）：把 Skill 文档当可训练权重，ReflACT 六阶段循环（Rollout→Reflect→Aggregate→Select→Update→Validate），零推理开销、跨模型复用、MIT
- **`mindforge-skill`**：多源采集 + 思维框架提炼（逆向工程→人物/主题 Skill 蒸馏）
- **`self-evolving-agent`**：9 原子工具 + 5 层记忆 + 技能结晶化协议 + 进化审计链

### 3.2 梦境系统 Dreaming Engine v2.4（来自 `Skill-hermes-dreaming`）

模拟生物睡眠的记忆巩固机制，**三维度梦境**：
1. **偏好梦境**：回复风格/工作风格/技术/沟通/投资偏好 + 矛盾检测 + 时间感知
2. **项目梦境**：架构决策/技术模式/里程碑/故障根因/代码质量/跨项目模式
3. **技能梦境**：工具使用频率/工作流模式/效率瓶颈/成功模式/新技能候选

**架构演进（重要）**：v2 从"Agent 手动梦境"升级为 **"Python handler + Cron 双触发"**——
`dream-keeper-idle` 每 30 分钟检测 CPU 空闲 >85% 时触发 `handler.py --auto`；每日 23:10 做完整三维度反思。
Agent 只做报告解读，不做重活。

**关键判断规则**（可直接复用）：
- 新洞察标准 = 此前 MEMORY.md 完全不存在，或状态实质变化
- 去重标准 = 同一模式不同日期出现**不算**新洞察
- L1 容量控制 = 活跃区 < 3000 bytes，最多 12 条导航索引
- **Cron 会话过滤** = 若搜索结果 80%+ 为 cron 轮次（source="cron"），直接判定无新洞察 → `[SILENT]`

### 3.3 自愈基础设施 Self-Heal 3.0（来自 `Skill-self-heal`）

三大模块闭环：**故障推理引擎 → 修复沙箱 → 经验学习闭环**

**执行铁律**（值得写进规范）：
- 不拖延，发现问题立即自主修复→验证→评估→记录→沉淀，不带错误继续
- 诊断完成 → `safety=safe` 的方案直接执行，**不逐步确认**
- 不能自动修复 → 立即推送告警，**不静默忽略**
- 任何环节出错 → 修复后继续，不放弃

故障模式库含 14 种模式；references 含 MEMORY.md 并发写入冲突、服务端口冲突、服务功能替代检测等手册。

### 3.4 Skill 库维护（来自 `Skill-skill-library-maintenanc...`）

**最有价值的坑**：**双目录结构**
```
~/.hermes/skills/           ← 根目录（官方标准）
~/.hermes/skills/skills/    ← 嵌套目录（冗余，会导致 skill_manage 报 "Skill not found"）
```
诊断：`find ~/.hermes/skills/ -name 'SKILL.md' | wc -l` 对比有 `name:` frontmatter 的数量。

**SOP 合规**：47 个 Skill 曾缺"步骤"章节、27 个缺"验证"章节 →
`fix_skill_sop.py` 按类别套模板（workflow=准备→执行→输出→异常；reference=明确目标→检索→整理→标注；config=读取→应用→验证→回滚；generic=接收→执行→返回），达成 98.7% 合规。

**脚本去重**：82 → 65（↓20.7%），合并 `evaluation_dashboard.py + evolution_dashboard.py → unified_dashboard.py`。

### 3.5 book-to-skill 方法论（来自 `Skill-book-to-skill`）

**核心理念：提取结构，不是写摘要。** 一本书的 Skill 应含：
- 命名框架（mental models）
- 可执行原则（决策规则）
- 技法（step-by-step）
- 反模式（避免什么、为什么）
- 声音校准（作者如何思考与表达）

**保留作者精确性**："The 5 Whys" 不能换成"多问几次为什么"。
**四模式**：Full Conversion / Analyze Only / Generate from Prior Analysis / Update-Fold-in。

### 3.6 Agent Reach 全网检索（来自 `Skill-agent-reach`）

17 平台统一 CLI，零 API Key：Exa 语义搜索、Jina Reader、GitHub、YouTube/Bilibili/抖音字幕、Reddit、V2EX、Twitter/X、微信公众号、RSS、LinkedIn。
统一入口：`bash scripts/agent-reach.sh <command> [args...]`

### 3.7 其他高价值条目

| 技能 | 要点 |
|------|------|
| `Skill-api-provider-integration` | 第三方 API 集成 6 步：发现模型→连通测试→响应格式检查→SDK 验证→配置写入→文档沉淀。**坑**：SenseNova 默认返回 `reasoning` 字段而非 `content`，需 `reasoning_effort: none` |
| `Skill-mcp` | MCP 配置。**坑**：`hermes mcp add --args` 在 npx + @scope 包名时 exit code 2，须手动编辑 config.yaml；`args: []` 不能为空 |
| `Skill-hermes-maintenance` | MCP 连接失败/MCP sqlite parking/Profile state.db 过大/临时文件清理 |
| `Skill-auto-hermes` | 新 Skill 自动评估 6 项检查清单；MCP 自动审查 4 步；搜索自动增强 |
| `Skill-turbovec-integration` | Turbovec 向量索引（基于 Google TurboQuant），百万级文档语义检索 |
| `Skill-continuous-learning` | Observer/Monitor/Planner/Tracker 四件套。**坑**：messages 表用 `timestamp`(REAL) 不是 `created_at` |

## 四、项目级知识（可读库中的项目文档）

### 4.1 BOSS-AI-R 混合推理架构（`hybrid_inference_architecture.md`）
三层路由：**L0 本地极速（<200ms，规则+缓存，成本0）→ L1 端侧（200ms~2s，RK182X NPU，Qwen3.8-27B INT4 / MiniCPM5-2B，成本0）→ L2 云端（2s~5s，DeepSeek V4.1 Flash）**
成本：1000 用户月 ≈¥1000，比纯云 ¥5000 **省 80%**。
隐私分级：声纹 AES-256 禁传云、谈判内容优先端侧+加密脱敏 90 天过期、用户画像仅本地。

### 4.2 DeepSeek V4.1 Flash 技术要点
Causal-Encoder-Decoder 非对称（输入激活 8B / 输出 16B，总参 552B MoE）；KV Cache 缩至 1/4，累计缩小 **437 倍**；峰谷定价（闲时 = 高峰 50%）；`deepseek-flash` 即 V4.1 Flash。

### 4.3 竞品：实在Agent
TARS 千亿自研 + ISSUT 屏幕语义理解（国家专利）+ 双模决策（AI 层创意拆解 / 规则层合规约束）。**已推出"商务谈判智能助手"（2026 新品）——与 BOSS-AI-R 正面竞争**。

### 4.4 Graph Memory 前沿
- **MemGraphRAG**（KDD 2026）：三层全局记忆（Schema 本体 / Fact 三元组 / Passage 原文段落）+ 双向索引 + 三 Agent 协作（抽取/冲突检测/冲突解决）。把 KG 构建从"逐块独立抽取"重新定义为"全局记忆与图谱的动态共演化"
- **GraMRAG**（arXiv 2609.14066）：图记忆 + 强化学习编排多智能体多步推理

## 五、跨库综合洞察（10 条）

1. **"专用小模型 + 边界执行"是端侧正解**：CUA-S1（706K 参数表单决策）与 DeepSeek 非对称架构同证——不必追求大而全
2. **记忆系统的分层是共识**：Tair 短期记忆栈 / MemGraphRAG 三层全局记忆 / Hermes 三层记忆 —— 均指向"热/温/冷"分层
3. **"提取结构而非摘要"是知识资产化的关键**：book-to-skill 的理念可直接用于 IMA 知识库 → 技能转化
4. **Cron 会话是信噪比陷阱**：梦境系统明确要求 80%+ cron 轮次时直接静默——这对我们的 autonomous-reporting 是直接印证
5. **双触发架构优于纯 Agent 驱动**：Dream Keeper v2 从"Agent 手动"改为"Python handler + Cron"，Agent 只解读报告——降低 token 消耗且更可靠
6. **Skill 文档可作为可训练权重**：skillopt-integrator 的 ReflACT 循环是 Skill 进化的新范式
7. **故障自愈必须"安全方案直接执行不逐步确认"**：与用户"完全授权"偏好一致
8. **订阅库的知识索引价值**：即使不能读全文，61 个订阅库的标题本身构成"AI 赛道知识地图"
9. **竞品已在行动**：实在Agent 已推商务谈判助手 —— BOSS-AI-R 的时间窗在收窄
10. **端侧成本优势明确**：混合推理省 80%，是"认知差变现 + 轻运营"商业模式的成本底座

## 六、可复用产物

| 产物 | 路径 |
|------|------|
| 知识库清单快照 | `ima_kbs_snapshot.json`（66 库） |
| 检索命中集 | `ima_search_hits.json`（678 条） |
| 可读库清单 | `ima_readable_kbs.json` |
| 抓取日志 | `fetch_log.json` |
| 原文下载 | `raw/`（20 篇） |
| 笔记下载 | `notes/`（88 篇，含 70 个 Skill） |
