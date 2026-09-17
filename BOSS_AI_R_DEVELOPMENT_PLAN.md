# BOSS-AI-R 开发排期与模块设计

> 创建日期：2026-09-16
> 基于：BOSS_AI_R_PRD_DETAILED.md
> 交付目标：V0.1 MVP（定州 50 家内测）

---

## 一、开发排期总表（12 周）

### 阶段一：基础框架（W1-2）

| 周次 | 模块 | 工作量 | 交付物 | 负责人 |
|---|---|---|---|---|
| W1 | 项目初始化 + 配置管理 | 3d | 项目骨架、配置系统、日志系统 | 架构师 |
| W1 | 数据库 schema 扩展 | 2d | 新表结构（negotiation/opportunity/decision_card/compliance_event） | 后端 |
| W2 | 用户认证 + 权限系统 | 3d | 注册/登录/角色权限/JWT | 后端 |
| W2 | API 框架搭建 | 2d | FastAPI 基础结构、中间件、错误处理 | 后端 |

### 阶段二：核心功能（W3-6）

| 周次 | 模块 | 工作量 | 交付物 | 负责人 |
|---|---|---|---|---|
| W3 | prompt_decider.py | 5d | 提示决策器（去重/分级/择时/打断保护） | AI 工程师 |
| W4 | compliance.py | 3d | 合规引擎（同意管理/权利响应/PIPIA） | 后端 |
| W4 | realtime_audio.py | 2d | 音频采集 + 降噪 + VAD | 客户端 |
| W5 | realtime_audio.py（续） | 5d | 流式 ASR + 说话人分离 + 端侧兜底 | 客户端 |
| W6 | acoustic_emotion.py | 5d | 声学情绪检测（F0/能量/语速/停顿） | AI 工程师 |

### 阶段三：业务功能（W7-9）

| 周次 | 模块 | 工作量 | 交付物 | 负责人 |
|---|---|---|---|---|
| W7 | billing.py | 3d | 四级订阅/配额管理/成本监控 | 后端 |
| W7 | 实时转写 API | 2d | WebSocket 实时转写接口 | 后端 |
| W8 | 会后五件套生成 | 5d | 纪要/商机/待办/决策卡/复盘 | AI 工程师 |
| W9 | 经营外脑集成 | 5d | 日报/财务体检/异常预警/决策追溯 | 后端 |

### 阶段四：集成测试（W10-12）

| 周次 | 模块 | 工作量 | 交付物 | 负责人 |
|---|---|---|---|---|
| W10 | 端到端集成测试 | 5d | 全链路测试用例 + 性能基准 | 测试 |
| W11 | UI/UX 优化 | 5d | 界面美化 + 交互优化 + 响应式设计 | 前端 |
| W12 | 内测准备 + 种子客户 | 5d | 内测包 + 种子客户跟进 + Bug 修复 | 全员 |

---

## 二、模块架构设计

### 2.1 分层架构

```
┌─────────────────────────────────────────────┐
│                  UI 层                        │
│  (ui/templates/*.html + static/css/js)       │
├─────────────────────────────────────────────┤
│                  API 层                       │
│  (api/routers/*.py + api/middleware/*.py)    │
├─────────────────────────────────────────────┤
│                  Service 层                   │
│  (modules/prompt_decider.py                  │
│   modules/realtime_audio.py                  │
│   modules/acoustic_emotion.py                │
│   modules/compliance.py                      │
│   modules/billing.py)                        │
├─────────────────────────────────────────────┤
│                  Data 层                      │
│  (graph_store.py + graph_schema.py)          │
├─────────────────────────────────────────────┤
│                  Infrastructure               │
│  (config.py + logger.py + security.py)       │
└─────────────────────────────────────────────┘
```

### 2.2 模块依赖关系

```
graph_store.py ← compliance.py ← billing.py
      ↑              ↑
graph_schema.py    prompt_decider.py
      ↑              ↑
observation_pack.py  realtime_audio.py
                   ↑
              acoustic_emotion.py
```

---

## 三、新增文件清单

```
sol_pi_engram_evolution/
├── modules/
│   ├── __init__.py
│   ├── prompt_decider.py          # P0: 提示决策器
│   ├── compliance.py              # P0: 合规引擎
│   ├── realtime_audio.py          # P1: 实时音频
│   ├── acoustic_emotion.py        # P2: 声学情绪
│   ├── billing.py                 # P1: 订阅计费
│   └── deployment.py              # P3: 部署配置
├── api/
│   ├── __init__.py
│   ├── app.py                     # FastAPI 应用
│   ├── deps.py                    # 依赖注入
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py                # 认证
│   │   ├── realtime.py            # 实时副驾
│   │   ├── brain.py               # 经营外脑
│   │   ├── compliance.py          # 合规
│   │   └── billing.py             # 计费
│   └── middleware/
│       ├── __init__.py
│       ├── tenant.py              # 租户隔离
│       ├── auth.py                # 认证中间件
│       └── logging.py             # 请求日志
├── ui/
│   ├── static/
│   │   ├── css/
│   │   │   └── main.css           # 主样式
│   │   ├── js/
│   │   │   ├── main.js            # 主交互
│   │   │   ├── realtime.js        # 实时副驾
│   │   │   ├── emotion.js         # 情绪曲线
│   │   │   └── graph.js           # 图谱可视化
│   │   └── images/
│   └── templates/
│       ├── base.html              # 基础模板
│       ├── dashboard.html         # 主控台
│       ├── realtime.html          # 实时副驾
│       ├── brain.html             # 经营外脑
│       ├── graph.html             # 知识图谱
│       ├── compliance.html        # 合规
│       ├── pricing.html           # 定价
│       └── roadmap.html           # 路线图
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # 测试配置
│   ├── test_prompt_decider.py     # 提示决策器测试
│   ├── test_compliance.py         # 合规引擎测试
│   ├── test_realtime_audio.py     # 实时音频测试
│   ├── test_acoustic_emotion.py   # 声学情绪测试
│   ├── test_billing.py            # 计费测试
│   └── test_api.py                # API 测试
├── config.py                      # 统一配置
├── logger.py                      # 日志系统
├── requirements.txt               # 依赖
└── README.md                      # 项目说明
```

---

## 四、各模块详细设计

### 4.1 prompt_decider.py（P0 优先）

**职责**：提示去重、分级、择时、打断保护

**核心类**：
- `PromptDecider`: 主决策器
- `PromptEvent`: 提示事件数据类
- `PromptQueue`: 提示队列管理
- `ChannelRouter`: 通道选择

**关键算法**：
- 去重：相似度 >0.85 合并
- 分级：L0(高)/L1(中)/L2(低)
- 择时：检测对方停顿点（VAD 端点后 500ms）
- 打断保护：对方说话中不推复杂建议

### 4.2 compliance.py（P0 优先）

**职责**：同意管理、录音指示、权利响应、PIPIA

**核心类**：
- `ComplianceEngine`: 合规引擎
- `ConsentManager`: 同意管理器
- `RetentionManager`: 数据保留管理
- `RightsResponse`: 权利响应

**关键流程**：
- 首次启动：协议+隐私政策双弹窗
- 每次录音：场景选择+告知模式
- 录音后：30/90 天过期自动删除
- 权利响应：15 工作日删除/去标识

### 4.3 realtime_audio.py（P1 优先）

**职责**：音频采集、降噪、VAD、流式 ASR、说话人分离

**核心类**：
- `AudioPipeline`: 音频流水线
- `AudioCapture`: 音频采集器
- `NoiseSuppressor`: 降噪处理器
- `VADDetector`: 端点检测
- `ASRServiceRouter`: ASR 服务路由
- `SpeakerSeparator`: 说话人分离

**关键流程**：
- 采集(10-20ms) → 降噪(RNNoise) → VAD → 编码(Opus) → wss 上行
- 下行：ASR 文本 → 分析 → 提示 → wss 下行 → 震动/手表

### 4.4 acoustic_emotion.py（P2 优先）

**职责**：声学特征提取、情绪维度计算、事件检测

**核心类**：
- `EmotionAnalyzer`: 情绪分析器
- `AcousticFeatureExtractor`: 声学特征提取
- `EmotionEventDetector`: 情绪事件检测

**关键指标**：
- 唤醒度 (Arousal): F0 基频 + 能量 + 语速
- 效价 (Valence): 语调 + 文本语义
- 确定度 (Confidence): 停顿时长 + 措辞

### 4.5 billing.py（P1 优先）

**职责**：四级订阅、配额管理、成本监控、渠道分润

**核心类**：
- `SubscriptionManager`: 订阅管理器
- `QuotaTracker`: 配额跟踪
- `CostMonitor`: 成本监控
- `ChannelPartner`: 渠道分润

**关键规则**：
- L0: 免费限次（月 3 次，每次 ≤20min）
- L1: 1980 元/月会后结构化（月 10h）
- L2: 9800-15800 元/年实时副驾
- L3: 39800-69800 元/年私有化+陪跑

### 4.6 deployment.py（P3 优先）

**职责**：多环境配置、数据驻留、安全策略

**核心类**：
- `DeploymentConfig`: 部署配置
- `DataResidencyManager`: 数据驻留
- `SecurityPolicy`: 安全策略

**关键配置**：
- 端侧：降噪/VAD/L0 关键词
- 省内云：阿里云华北3（张家口）
- 私有化：Qwen + vLLM 一体机
- 混合脱敏：NER 去标识后上云

---

## 五、开发规范

### 5.1 代码规范

- Python 3.11+
- 类型注解：所有函数参数和返回值
- Docstring：Google 风格
- 命名：snake_case（变量/函数）、PascalCase（类）
- 行宽：120 字符
- import 排序：stdlib → 第三方 → 本地

### 5.2 测试规范

- pytest 框架
- 每个模块 ≥5 个测试用例
- 测试覆盖率 ≥80%
- 异步测试使用 pytest-asyncio
- Mock 外部服务（ASR/LLM API）

### 5.3 API 规范

- RESTful + WebSocket
- 版本控制：/api/v1/
- 错误格式：`{"error": {"code": "...", "message": "..."}}`
- 分页：`?page=1&size=20`
- 过滤：`?status=active&tenant_id=xxx`

### 5.4 Git 规范

- main: 稳定分支
- develop: 开发分支
- feature/*: 功能分支
- hotfix/*: 修复分支
- commit: `feat/fix/refactor: 描述`

---

## 六、验收标准

### 6.1 代码质量

- [ ] 所有模块测试覆盖率 ≥80%
- [ ] 无 PEP8 警告（flake8）
- [ ] 无类型错误（mypy）
- [ ] API 文档自动生成（Swagger）

### 6.2 性能指标

- [ ] 安静近场 ASR CER ≤8%
- [ ] 关键词预警 P90 ≤2.5s
- [ ] 端到端提示延迟 P90 ≤10s
- [ ] 并发支持 ≥100 路实时流

### 6.3 安全合规

- [ ] 水平越权 100% 拦截
- [ ] 垂直越权 100% 拦截
- [ ] 声纹数据会后即毁
- [ ] 传输 TLS 1.2+
- [ ] 存储 AES-256

---

## 七、风险与应对

| 风险 | 等级 | 应对 |
|---|---|---|
| 声学情绪准确率不达标 | 中 | V0.1 仅做触发器，V0.2 再优化 |
| 第三方 ASR 延迟高 | 高 | 自建 FunASR 兜底方案 |
| 安卓后台被杀 | 中 | 厂商保活引导页 + 前台服务 |
| 合规审查不通过 | 高 | 提前律师审查 + PIPIA 留档 |

---

> 本排期基于 5 人团队（1 架构 + 2 后端 + 1 客户端 + 1 前端）估算
