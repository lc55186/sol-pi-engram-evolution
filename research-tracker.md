# 研究追踪 — 2026-09-16

> 来源: Researcher Bot 自动检索报告 `~/Desktop/research/2026-09-16.md`
> IMA 归档: 知识库「科技公司项目」→ `AI-Agent-Research-2026-09-16.md`

---

## 与 SoL-Pi × Engram 项目的关联发现

### 1. Engram 双过程记忆架构（直接相关）

**来源**: arXiv:2606.09900 | GitHub: EngramMemory/engram-memory (36 ⭐)

| 特性 | 本项目对应模块 | 差距分析 |
|------|--------------|---------|
| System-1 热写入 (sub-50ms) | `graph_store.py` + `observation_pack.py` | 当前 SQLite 写入约 200ms，需优化 |
| System-2 异步整合 | `graph_extractor.py` | 已实现启发式提取，但缺少时序知识图谱 |
| 双时序知识图谱 | `graph_schema.py` | 当前为静态图谱，缺少时间维度 |
| 混合检索 (dense+BM25+图谱+RRF) | `graph_retriever.py` | 当前仅关键词检索，需增加向量+BM25 |
| MCP 协议支持 | 待开发 | 需新增 MCP server 模块 |

**行动项**:
- [ ] 评估 Engram 的 RRF 融合检索是否可替换当前 `graph_retriever.py`
- [ ] 时序知识图谱设计参考 Engram 的 as-of 过滤机制
- [ ] MCP server 模块规划（对接 AAIF 标准）

---

### 2. 多 Agent 编排标准化（架构参考）

**关键数据**: 78% 企业已部署多 Agent，MCP+A2A 加入 Linux Foundation AAIF

**对本项目的影响**:
- 当前 Pipeline 为单 Agent 架构，未来需支持 Orchestrator-Worker 模式
- Anthropic "Dreaming" 机制（定时处理历史会话）可参考用于 `evolution_interface.py`
- Token 消耗 15× 问题需纳入边缘端资源预算

---

### 3. RK3588 生态成熟（硬件平台确认）

**关键信息**:
- RK3588: 6 TOPS NPU, 可扩展至 58 TOPS via PCIe
- RKLLM 已支持 DeepSeek-R1 7B 本地推理
- 开发板 $149-250，边缘盒子 $99-199

**对本项目的影响**:
- 硬件选型确认：RK3588J 边缘盒子 ($99-199) 为最优部署目标
- DeepSeek-R1 7B 可作为端侧推理模型
- 需跟进 RKLLM 的 NPU 支持进展（当前仅 Vision 模型，RK3576 已支持 LLM）

---

### 4. Token 组合压缩（推理优化）

**关键数据**: Entropy Gate 实现 88-96% Token 削减

**对本项目的影响**:
- `context_compactor.py` 当前为规则压缩，可参考 Entropy Gate 的熵淬火机制
- 外部记忆 + 熵淬火乘法公式: `R_total = 1-(1-R_mem)(1-R_quench)`
- 若应用于端侧，可显著降低 DeepSeek 7B 的推理负载

---

## 趋势研判（6-18 个月）

| 趋势 | 置信度 | 对项目影响 |
|------|--------|-----------|
| 双时序图谱记忆成为标准 | 高 | 必须纳入下一版本架构 |
| MCP/A2A 标准化完成 | 高 | 需实现 MCP server |
| RK3588 支持 7B LLM 推理 | 已部署 | 可直接用于生产 |
| 组合式上下文压缩普及 | 中高 | 6 个月内需集成 |
| 自进化记忆进入生产 | 中 | 12-18 个月规划 |

---

## 下一步行动

1. **本周**: 评估 Engram 检索模块替换可行性
2. **本月**: 设计 MCP server 模块接口
3. **本季**: 集成 Entropy Gate 压缩机制到 `context_compactor.py`
4. **长期**: 跟踪 RKLLM NPU 支持进展，规划 7B 模型端侧部署

---

# 更新 — 2026-09-17

## 新增行动项

5. **本周**: 启动微信小程序开发（P1-8 PRD 已完成 → `BOSS_AI_R_MINIAPP_MVP.md`）
6. **本月**: 对接企查查/天眼查 API（小程序 MVP 依赖）
7. **持续**: 跟踪 NBBOSS+WorkBuddy 生态联盟动态（威胁等级 🔴高）
8. **Q3**: RK1860 正式发布后评估对部署路线的影响

## 竞品动态更新

| 竞品 | 9月动态 | 威胁变化 |
|------|---------|---------|
| NBBOSS+WorkBuddy | 9/2 生态合作正式落地，"决策+执行"闭环形成 | ⬆️ 生态锁定加强 |
| 瑞芯微 | RK1860 Q3 发布确认，13B 级端侧推理 | ⬆️ 硬件路线更清晰 |
| 微信 AI | "小微"内测，AI 小程序成长计划 | ⬆️ 小程序机会窗口开启 |
