# Agent-S × BOSS-AI-R 研究报告

> 研究日期：2026-09-19
> 来源：https://github.com/simular-ai/Agent-S

---

## 1. 项目概况

| 维度 | 内容 |
|------|------|
| **名称** | Agent-S / Sai |
| **厂商** | Simular AI |
| **定位** | 开源计算机使用 Agent 框架 |
| **核心理念** | 让 AI 像人一样操作电脑：看屏幕 → 理解界面 → 规划步骤 → 执行操作 |
| **GitHub** | https://github.com/simular-ai/Agent-S |
| **Stars** | 13,000+ (Trending) |
| **版本** | v0.2.5+ (gui-agents pip 包) |

---

## 2. 核心架构

### 2.1 AgentS3 主 Agent

```
用户指令 → 截图观察 → 推理规划 → 动作输出
                ↑              ↓
             屏幕截图 ← 执行操作（点击/输入/滚动）
```

### 2.2 OSWorldACI (Grounding Agent)

将 Agent 的高级动作翻译为可执行的 Python/pyautogui 代码：
- 坐标定位
- 点击/输入/滚动
- 多步任务分解

### 2.3 LocalEnv (可选)

本地代码执行环境：
- Python / Bash 代码执行
- 数据处理、文件操作、系统自动化
- 安全警告：执行任意代码，需可信环境

---

## 3. 关键能力

### 3.1 视觉感知
- 屏幕截图分析
- UI 元素识别
- 状态变化检测

### 3.2 操作能力
- 鼠标点击（坐标精确）
- 键盘输入（支持快捷键）
- 滚动浏览
- 拖拽操作

### 3.3 推理能力
- 多步任务规划
- 错误恢复
- 反思机制（Reflection Agent）

---

## 4. 性能基准

| Benchmark | 得分 | 备注 |
|-----------|------|------|
| OSWorld | 72.6% | 首次超越人类水平 (~72%) |
| OSWorld 2.0 (Sai) | 73% | 击败 GPT-5 Sol (62.57%) |
| WindowsAgentArena | 56.6% | 3-rollout行为克隆 |
| AndroidWorld | 71.6% | 从68.1%提升 |

---

## 5. 竞品对比

| 项目 | Agent-S | Claude Computer Use | OpenAI CUA | Mano-P |
|------|---------|-------------------|------------|--------|
| 开源 | ✅ MIT | ❌ 闭源 | ❌ 闭源 | ✅ Apache-2.0 |
| 本地部署 | ✅ | ❌ 云端 | ❌ 云端 | ✅ 完全本地 |
| 模型无关 | ✅ 多模型 | Claude only | GPT only | 自研GUI-VLA |
| Android支持 | ✅ | ❌ | ❌ | ✅ |
| 端侧推理 | ✅ vLLM | ❌ | ❌ | ✅ |

---

## 6. 安装与配置

### 6.1 基础安装
```bash
pip install gui-agents
# 或开发模式
git clone https://github.com/simular-ai/Agent-S.git
cd Agent-S && pip install -e .
```

### 6.2 Tesseract OCR（可选）
```bash
# macOS
brew install tesseract

# Ubuntu
sudo apt install tesseract-ocr
```

### 6.3 API 配置
```bash
# ~/.bashrc 或 ~/.zshrc
export OPENAI_API_KEY=<your_key>
export ANTHROPIC_API_KEY=<your_key>
export HF_TOKEN=<your_hf_token>
```

### 6.4 本地模型（vLLM）
支持 HuggingFace Inference Endpoints、TGI、Open Router、vLLM

---

## 7. 使用方式

### 7.1 CLI
```bash
agent_s \
    --provider openai \
    --model gpt-5-2025-08-07 \
    --ground_provider huggingface \
    --ground_url http://localhost:8080 \
    --ground_model ui-tars-1.5-7b \
    --grounding_width 1920 \
    --grounding_height 1080
```

### 7.2 Python SDK
```python
from gui_agents.s3.agents.agent_s import AgentS3
from gui_agents.s3.agents.grounding import OSWorldAC

# 初始化 grounding agent
grounding_agent = OSWorldAC(
    engine_params_for_generation=engine_params,
    engine_params_for_grounding=grounding_params,
    width=1920,
    height=1080
)

# 初始化 Agent S3
agent = AgentS3(
    engine_params,
    grounding_agent,
    platform="linux",  # "darwin", "windows"
    max_trajectory_length=8,
    enable_reflection=True
)

# 执行任务
screenshot = pyautogui.screenshot()
obs = {"screenshot": screenshot}
instruction = "Close VS Code"
info, action = agent.predict(instruction=instruction, observation=obs)
exec(action[0])
```

---

## 8. BOSS-AI-R 集成方案

### 8.1 Agent-S 对 BOSS-AI-R 的价值

| 应用场景 | Agent-S 作用 |
|---------|-------------|
| **安卓模拟器操作** | 通过 ADB 截图+坐标操作，自动化测试 APK |
| **桌面端辅助** | 老板用电脑时，Agent 自动识别屏幕并提示 |
| **自动化测试** | GUI 自动化回归测试，验证 APK 功能 |
| **数据录入** | 自动抓取 CRM/ERP 数据写入图谱 |

### 8.2 集成架构

```
┌─────────────────────────────────────────────┐
│                 BOSS-AI-R 系统                │
├─────────────────────────────────────────────┤
│  Android APP ←→ Server ←→ Desktop Agent     │
│       ↑              ↑           ↑          │
│    ADB截图      WebSocket    Agent-S         │
│    坐标操作     实时通信    屏幕操作          │
└─────────────────────────────────────────────┘
```

### 8.3 具体实现路径

**路径一：APK 自动化测试**
1. 安卓模拟器运行 BOSS-AI-R APK
2. Agent-S 通过 ADB 获取屏幕截图
3. 识别界面元素并自动操作
4. 验证录音、转写、预警功能

**路径二：桌面端实时辅助**
1. 电脑上运行 Agent-S 观察屏幕
2. 检测会议软件（Zoom/腾讯会议）
3. 叠加 BOSS-AI-R 提示层
4. 实时语音转写+预警（与手机 ASR 互补）

**路径三：数据自动采集**
1. Agent-S 自动登录企业 CRM/ERP
2. 抓取客户数据、订单数据
3. 写入 SoL-Pi 图谱知识库
4. 经营分析数据自动更新

---

## 9. 技术挑战与解决方案

### 9.1 paddlepaddle 依赖问题
**问题**：`gui-agents` 依赖 `paddlepaddle`，Python 3.14 暂不支持
**解决方案**：
1. 使用 Python 3.11~3.13 环境
2. 等待 paddlepaddle 更新（已在开发 cp314 支持）
3. 使用 Docker 容器隔离环境

### 9.2 模型兼容性
**推荐配置**：
- 主模型：GPT-5 / Claude Sonnet 4.5 / Qwen3-72B
- Grounding：UI-TARS-1.5-7B（端侧友好）
- 支持完全本地推理（vLLM）

### 9.3 延迟问题
**挑战**：截图→推理→操作 链路延迟
**优化**：
- 使用 UI-TARS 等专用 Grounding 模型（<500ms）
- 本地 vLLM 推理避免网络延迟
- 截图分辨率自适应（1920×1080 → 1000×1000）

---

## 10. 实施优先级

| 优先级 | 任务 | 工作量 | 依赖 |
|--------|------|--------|------|
| **P0** | 环境搭建（Python 3.11 + gui-agents） | 1-2天 | paddlepaddle |
| **P0** | 安卓模拟器 ADB 对接 | 2-3天 | ADB + scrcpy |
| **P1** | APK 自动化测试脚本 | 3-5天 | Agent-S + Airtest |
| **P1** | 桌面端实时辅助原型 | 5-7天 | Electron + Agent-S |
| **P2** | 企业系统集成 | 7-10天 | CRM/ERP API |

---

## 11. 参考资源

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/simular-ai/Agent-S |
| README | https://github.com/simular-ai/Agent-S/blob/main/README.md |
| Agent S3 论文 | https://arxiv.org/abs/2510.02250 |
| Agent S2 论文 | https://arxiv.org/abs/2504.00906 |
| Agent S1 论文 | https://arxiv.org/abs/2410.08164 |
| pip 包 | https://pepy.tech/projects/gui-agents |
| Discord | https://discord.gg/E2XfsK9fPV |

---

*V1.0 | 2026-09-19*
