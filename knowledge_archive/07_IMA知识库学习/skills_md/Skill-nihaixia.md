# Skill-nihaixia

***

name: nihaixia-tcm

description: |

倪海厦视角的中医 AI Agent Skill，融合经方辨证、药物查询、临床医案与知识图谱。

核心诊断能力：37个中医术语、12个六经公式、12个伤寒方剂、9种中药、4项舌诊编码、

6类临床医案，可直接诊断推理 + 知识检索。SQLite+FTS5 本地知识库，毫秒级响应。

适用场景：中医学习/咨询建议/学术研究/辅助诊断视角参考。

适用平台：Hermes / Claude Code / Codex / OpenClaw。

trigger\_keywords:

* 倪海厦
* 海厦视角
* 中医倪海厦
* 经方思维
* 倪海厦会怎么看
* 倪师
* 中医诊断
* 六经辨证
* 方剂查询
* 中药查询
* 伤寒论
* 金匮要略
* 医案

***

# 倪海厦中医 Agent Skill v1.0

## 概述

本 Skill 基于对 GitHub 两个核心仓库（`jangviktor-web/nihaixia` v2.1.0 + `JuneYaooo/nihaisha-nishi-tcm`）

深度逆向工程分析后重建，采用 **SQLite + FTS5 + 规则路由** 架构，

替代原始 Markdown+Grep 方案，实现毫秒级检索与结构化诊断推理。

## 数据规模

| **维度** | **数量**       | **来源**               |
| ------ | ------------ | -------------------- |
| 六经诊断公式 | 12           | nihaixia 8个 + 倪氏基础公式 |
| 伤寒方剂   | 37（12基准+可扩展） | 伤寒论129条 + 金匮23篇      |
| 中药     | 9基准（345可扩展）  | 神农本草经                |
| 针灸穴位   | 8基准（361可扩展）  | 针灸大成                 |
| 临床医案   | 3基准（849可扩展）  | nihaixia cases       |
| 证据页    | 不可加载（离线）     | nihaisha 3080 PDF页   |

## 环境要求

* Python 3.10+
* SQLite 3.40+（含 FTS5 扩展）
* 安装依赖：仅 Python 标准库

## 文件结构

```
nihaixia/
├── SKILL.md                    # 本文件
├── knowledge/
│   ├── nihaixia.db             # SQLite 知识库（自动生成）
│   ├── sync_state.json         # 增量同步状态（模块 SHA）
│   └── sync_log.txt            # 同步操作日志
├── scripts/
│   ├── init_db.py              # 知识库初始化与种子数据
│   ├── extract_data.py         # 数据抽取扩展
│   ├── sync_db.py              # 重建索引+数据修复
│   ├── query_nihaixia.py       # CLI 查询工具
│   ├── nihaixia_sync.py        # 增量同步脚本（v1.1 新增）
│   └── test_nihaixia.py        # 完整测试套件
└── references/
    └── diagnosis_formulas.md   # 六经公式源码说明
```

## 快速开始

### 1. 首次初始化

```bash
cd nihaixia
python3 scripts/init_db.py
```

### 2. 六经辨证诊断

```bash
python3 scripts/query_nihaixia.py diagnose "恶寒发热无汗头项强痛"
python3 scripts/query_nihaixia.py diagnose "发热不恶寒反恶热汗出烦渴" --channel 阳明
```

### 3. 方剂查询

```bash
python3 scripts/query_nihaixia.py formula "小柴胡汤"
python3 scripts/query_nihaixia.py herb "附子"
python3 scripts/query_nihaixia.py case "肺癌"
```

### 4. 全文搜索

```bash
python3 scripts/query_nihaixia.py "失眠多梦";
python3 scripts/query_nihaixia.py search "方剂 上火";
python3 scripts/query_nihaixia.py search "药物 有毒";
```

### 5. 安全检查

```bash
python3 scripts/query_nihaixia.py safe --text "处方：麻黄汤"
python3 scripts/query_nihaixia.py safe --text "剂量：麻黄9克 桂枝6克"
```

### 6. 增量同步 (v1.1 新增)

```bash
# 手动触发增量同步
cd nihaixia && python3 scripts/nihaixia_sync.py

# 仅查看状态，不同步
python3 scripts/nihaixia_sync.py --dry-run

# 查看同步日志
cat knowledge/sync_log.txt

# 查看同步状态
cat knowledge/sync_state.json
```

**工作原理**:

1. 请求 GitHub API 获取 `modules/` 下 9 个文件的最新 commit SHA
2. 与本地 `sync_state.json` 对比，检出变更文件
3. 下载内容，按文件类型解析（方剂/药材/伤寒/金匮/医案/梁冬）
4. SQLite UPSERT 入库 + FTS5 索引重建
5. 更新状态文件

**Cron 定时同步** (每日 03:00):

```bash
# 已在 Hermes cron 中配置，job_id: c176273e80b2
# 手动触发:
cd ~/.hermes/skills/nihaixia && python3 scripts/nihaixia_sync.py
```

**数据流向**:

```
GitHub (jangviktor-web/nihaixia:modules/*.md)
    ↓ API (commit SHA 检测)
本地 (sync_state.json 增量比对)
    ↓ 下载变更文件
Parser (regex 抽取: 方剂/药材/伤寒/金匮/医案/梁冬)
    ↓ UPSERT
SQLite (nihaixia.db) + FTS5 索引重建
```

## 六经辨证诊断公式（核心）

### 公式结构

```
IF 症状集合 {S1, S2, ...} ∈ 诊断阈值
   AND 脉象 ∈ {浮, 沉, ...}
   AND 舌象 ∈ {淡白, 红, ...}
THEN 六经归属 = 太阳/阳明/少阳/太阴/少阴/厥阴
   推荐方剂 = 方剂名 (置信度 N%)
   加减方向 = {...}
```

### 临床路径（七步走）

1. **定表里**: 恶寒发热并见 → 表证；但热不寒 → 里证
2. **分阴阳**: 三阳病（实热）vs 三阴病（虚寒）
3. **辨寒热**: 口渴、二便、舌脉
4. **判传变**: 太阳→阳明→少阳→太阴→少阴→厥阴
5. **审体质**: 气血阴阳偏颇
6. **选方剂**: 经方原方 + 加减
7. **精细加减**: 兼变症对应的药物调整

## 六经辨证决策树

```
发热恶寒?
├─ 是 → 有汗?
│  ├─ 是 → 桂枝汤证 (太阳中风)
│  └─ 否 → 麻黄汤证 (太阳伤寒)
│
└─ 否 → 但热不寒?
   ├─ 是 → 大汗大渴?
   │  ├─ 是 → 白虎汤证 (阳明经)
   │  └─ 否 → 腹满便秘?
   │     ├─ 是 → 三承气汤 (阳明腑)
   │     └─ 否 → 小柴胡汤 (少阳)
   │
   └─ 否 → 寒热错杂?
      ├─ 口渴+下利 → 少阴/厥阴
      └─ 脉微细 → 少阴寒化
```

## 药物安全分级

### ⚠️ 有毒药材（自动触发安全警告）

附子、乌头、细辛、硫磺、巴豆、甘遂、大劕、芫花、水蛭、虻虫、硃砂、雄黄、铅丹、砒

### 🔴 禁忌组合（常见十九畏）

* 硫黄畏朴硝，水银畏砒霜，狼毒畏密陀僧
* 巴豆畏牵牛，丁香畏郁金，牙硝畏三棱
* 川乌草乌畏犀角，人参畏五灵脂，官桂畏赤石脂

### 🚫 自动拒答场景

* 个人化诊断 (要求症状分析 → 提示但拒绝处方)
* 毒麻药方 (含附子、马钱子、砒霜等 → 直接拒绝)
* 儿科孕产 (特殊人群 → 附加双重警告)
* 急诊情形 (胸痛、昏厥、呼吸困难 → 120提示)

## 交互工作流

### 流程 1: 学习咨询 (默认)

用户 → 触发词激活 → Skill 加载 → 检索知识库 → 表格化展示方证对比

### 流程 2: 辅助诊断视角

用户 → 输入症状 → 六经公式匹配 → 分类置信度排序 → 输出"学习参考"

### 流程 3: 方剂/中药

用户 → 输入方剂/药名 → SQL 查询 → 输出 组成/主治/禁忌/方论

### 流程 4: 医案检索

用户 → 输入病名 → FTS5 搜索 → 输出 病例摘要 + 处方分析

## 安全边界（强制）

1. **所有输出以"倪海厦课程学习参考"为边界**
2. **禁止输出** todo list/伪代码/可执行操作步骤
3. **高风险内容** 自动折叠 + 警告转诊
4. **所有引用** 标注原始来源 (伤寒/金匮/内经/本草/医案)
5. **对外传输** API 调用时脱敏症状/舌象数据
6. **每轮诊断** 必须包含 disclaimer 文本

## 禁止清单

* 禁止输出个人化诊断结论
* 禁止给出可执行的用药剂&#x91CF;_&#x79D2;&#x6570;_&#x9891;率
* 禁止输出针刺穴位定位的实操描述
* 否认 "可以替代医师" 的暗示
* 否认 "AI 开方" 的暗示

## 扩展路径

知识库结构预留了扩展字段，支持增量添加：

* 方剂库: 从 12 扩展到 2000+（后世经方+时方）
* 药材库: 从 9 扩展到 800+（本章纲目备要）
* 医案库: 从 3 扩展到 1000+（历代名医医案）

## 版本历史

| **版本** | **变化**                                                  |
| ------ | ------------------------------------------------------- |
| v1.0   | 初始重建，基于逆向工程分析                                           |
| ​      | 融合 nihaixia v2.1.0 诊断公式 + nihaisha-nishi-tcm 证据追溯       |
| ​      | SQLite+FTS5 替代 Markdown+Grep                            |
| v1.1   | **增量数据同步自动化**                                           |
| ​      | 新增 `nihaixia_sync.py`（GitHub API diff → 解析入库 → FTS5 重建） |
| ​      | 新增 `sync_state.json`（模块 SHA 跟踪，支持断点续传）                  |
| ​      | 新增 `sync_log.txt`（带时间戳的操作日志）                            |
| ​      | Cron 定时同步（每日 03:00，job\_id: c176273e80b2）               |
| ​      | 数据规模扩展：梁冬对话 5→286 条，金匮要略 12→13 篇                        |
