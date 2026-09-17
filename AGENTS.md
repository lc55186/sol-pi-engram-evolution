# SoL-Pi × Engram 融合系统项目规则

## 项目概述
RK3588 端侧 AI 智能体解决方案，融合 NVIDIA SoL-Pi 效率机制与 DeepSeek Engram 图谱记忆。

## 目录结构
```
C:/Users/liuchao/Desktop/sol-pi-engram-evolution/sol_pi_engram_evolution/
├── graph_schema.py          # 阶段 0：节点类型定义
├── graph_store.py           # 阶段 1：SQLite 图谱存储
├── observation_pack.py      # 阶段 1：原文归档 + handle 管理
├── observation_pack_ccr.py  # CCR 缓存层
├── graph_extractor.py       # 阶段 1：启发式节点提取
├── evidence_verifier.py     # 阶段 1：证据核验
├── graph_retriever.py       # 阶段 2：按需检索
├── context_manager.py       # 阶段 2：上下文管理 + SoL-Pi 接口
├── action_fusion.py         # 阶段 2：确定性流合并
├── context_compactor.py     # 阶段 2：经济学压缩
├── value_evaluator.py       # 阶段 3：节点价值评估
├── routing.py               # 阶段 4：短对话轻量路由
├── evolution_interface.py   # 阶段 5：自主演进接口
├── pipeline.py              # 主入口，串联所有模块
├── format_converter.py      # 格式扩展：CSV/JSON/XML
├── batch_processor.py       # 格式扩展：批量处理
├── pipeline_tool.py         # 格式扩展：管道/自动化
├── deploy_tool.py           # 格式扩展：部署/工具化
├── content_type_detector.py # 内容类型检测
├── context_tracker.py       # 跨轮追踪
├── compression_verifier.py  # 压缩质量验证
└── tests/                   # 测试目录
```

## 技术约束

### Python 开发
- **动态导入**：跨目录导入必须使用 `importlib.util.spec_from_file_location`，不要用 `sys.path`
- **中文冒号**：正则表达式必须同时匹配半角 `:` 和全角 `：`，使用 `[\s:：]` 模式
- **测试导入**：测试文件在 `tests/` 中运行，需动态加载兄弟模块

### 数据库
- 使用 SQLite，路径通过 `db_path` 参数注入
- 测试时使用临时数据库，避免污染生产数据

### 归档系统
- 归档根目录：`./observations`（可通过配置修改）
- 按日期分目录：`YYYY-MM-DD`
- 每个归档条目有 `.meta.json` 元数据文件

## 操作限制

### 禁止
- 不要修改 `tests/__init__.py` 的内容（已配置好）
- 不要跨目录直接 `import` 模块
- 不要在测试中硬编码生产数据库路径
- 不要修改 `meta.json` 的 `version` 字段（IMA 技能用）

### 必须
- 新模块必须创建对应的 `tests/test_*.py`
- 所有节点操作必须经过 `EvidenceVerifier` 核验
- 归档操作必须生成 `.meta.json` 元数据
- 价值评估必须支持时间注入（用于测试）

## 交付要求

### 代码规范
- 文件头包含 `#!/usr/bin/env python` 和 `# -*- coding: utf-8 -*-`
- 模块 docstring 说明阶段和职责
- 类和方法必须有 docstring

### 测试规范
- 测试函数以 `test_` 开头
- 每个模块至少有 5 个测试用例
- 测试必须独立运行，不依赖其他测试的状态
- 使用 `pytest` 运行：`cd tests && pytest test_xxx.py -v`

### 提交前检查
- 运行 `python -m pytest tests/ -v` 确保全部通过
- 检查新文件是否已添加到 `.project_manifest.md`
- 更新 `pipeline.py` 如果新增模块需要串联

## 常用命令

```bash
# 运行所有测试
cd C:/Users/liuchao/Desktop/sol-pi-engram-evolution/sol_pi_engram_evolution
python -m pytest tests/ -v

# 运行单个模块测试
python -m pytest tests/test_graph_store.py -v

# 运行 Pipeline
python pipeline.py query "测试查询"
python pipeline.py archive ./test_file.txt
python pipeline.py stats
```

## 环境
- Windows 11 + MSYS bash
- Python 3.11.16（Hermes venv）
- 无 `python3`、`pip`、`pipx`（使用 `uv`）
- 项目 venv：`C:\Users\liuchao\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe`
