# CUA（trycua/cua）研究分析报告

> 生成时间：2026-10-03
> 来源：头条「卷积不内卷」《开源一年狂揽2.7万星，这个项目要给AI配一台真电脑》
> 仓库：https://github.com/trycua/cua （27,812 星 / 1,960 fork / MIT / Rust 核心）
> 公司：Cua AI（Y Combinator X25 批次）

## 一、它解决什么问题

让 AI 大模型"有手有脚"。模型会说不会做（没有眼睛看屏幕、没有手点鼠标），
CUA 提供一套**开源、可自托管**的计算机操作基础设施——不造模型，只做"电脑 + 手 + 考场"。
与 OpenAI CUA（闭源模型）路线相反：模型自己带（Claude/GPT/开源都行），它只提供机器、驱动、小模型、基准。

## 二、五件套

| 组件 | 作用 | 本机可落地性 |
|------|------|-------------|
| **Cua Driver** | 跨 macOS/Win/Linux 操作原生应用+浏览器；CLI/MCP/SDK 三种接法；"后台投递"不抢焦点 | ✅ 已装（v0.21→0.23.2），守护进程运行中 |
| **Cua Fleets / Spaces** | 云上申领隔离 Linux 桌面，按秒计费，任务完即销毁 | ⚠️ 需付费云账户 |
| **CUA-S1** | "系统1"小型专用模型，对候选动作打分（表单场景），一次前向出结果 | ⚠️ 权重在 HF，仅表单窄场景 |
| **Lume** | Apple Silicon 本地跑 macOS/Linux VM（原生性能 97%） | ❌ 需 Mac |
| **Cua Bench** | 建任务、跑 agent、导出轨迹、评测（免 VM/Docker/Key 的模拟任务） | ✅ 已装 v0.3.0 |

## 三、本机实测结果（2026-10-03）

### 1. Cua Bench（v0.3.0，uv 安装成功）
- `cb` CLI 可用，命令族：run/interact/agent/platform/task/trace/dataset
- 内置任务模板 `starter_env`（写一个词到文件，oracle 解 + 评测器）
- **默认 backend = local-gvisor 容器**（ghcr.io/trycua/linux:24.04）
- ⛔ 容器路径失败：gVisor 不支持 Windows；本机 Docker Desktop 守护进程锁在交互式
  会话（Session 0 无法拉起，socket "Access is denied"）

### 2. 评分机制验证（绕开容器，内存 fake 沙箱）
用 cua-bench 自带解释器加载内置任务，造内存 fake DesktopSession 跑 oracle→evaluate：
- word='hello'：解前 reward=0.0 → oracle 解后 reward=1.0 ✓
- word='bench'：解前 0.0 → 解后 1.0 ✓
- `cb.Task` 数据结构可正常构造 ✓
- **结论：评测器的"oracle 0→1.0"闭环逻辑正确，机制可信**（只是真实容器/VM 沙箱
  需 Mac 或可用的 Docker 环境才能跑完整任务）

### 3. Cua Driver（核心交付物，全部通过）
- 安装成功：`cua-driver` 0.21.0（health_report 显示已自动更新到 0.23.2）
- 守护进程运行中：socket `\\.\pipe\cua-driver`，pid 10816
- `health_report`：binary_version / platform_supported / session_active 全 pass
- 工具清单（AI 的"手"）：click/double_click/drag/hotkey/launch_app/kill_app/
  clipboard/browser_click/browser_type/get_desktop_state/...
- **真·操作验证**：
  - `get_desktop_state` → 截到 1920×1080 主屏（PNG base64）✓
  - `list_windows` → 枚举出真实在跑的窗口：Hermes、WorkBuddy、设置（含 pid/坐标/边界）✓
- 与 Hermes 既有 `cua-driver computer_use` 工具为**同一套驱动**，已打通

### 4. Lume
- ❌ 仅 Apple Silicon 可用，本机 Windows 无法验证（记录为限制）

## 四、冷静评价与边界

1. **计算机操作仍是最难的落地场景**：界面千变万化，一个弹窗就能卡死 agent，
   误操作可能真删文件。仓库有 1020 个 open issues，仍在快速迭代，远非"装上即用"。
2. **CUA-S1 只覆盖表单窄场景**，权重/数据集有独立 license，感知扩展（OmniParser）
   是 AGPL，商用前逐块看 LICENSE。
3. **后台投递是关键卖点**：agent 操作时不移动你的指针、不抢窗口焦点，
   你可以同时正常用这台电脑。
4. **本机可立即复用的**：Cua Driver（已跑通）+ Cua Bench 评分机制（已验证）。
   要跑完整 agent 任务闭环，需 Mac（Lume/VM）或可用的 Docker 容器环境。

## 五、对本项目的可借鉴点

- **RK3588 端侧 / BOSS-AI-R**：CUA 的"隔离机器 + 驱动 + 专用小模型 + 考场"分层思路，
  与端侧智能体架构高度同构；驱动层"后台投递不抢焦点"可直接借鉴到机器人/桌面辅助。
- **Cua Bench 任务化评测**：把"AI 操作电脑"变成可量化打分的 benchmark，
  可用于 SoL-Pi 融合系统的端侧操作类任务验收。
- **已打通 Hermes 的 computer_use 工具链**：本机 `cua-driver` 即 Hermes
  `computer_use` 的底层驱动，后续 GUI 自动化任务可直接复用。

## 六、待办 / 受限项

- [ ] 完整 agent 闭环任务（需 Mac 或可用 Docker，本机受限）
- [ ] CUA-S1 表单模型下载与本地推理测试（HF 权重，需网络）
- [ ] Fleets 云桌面（需 Cua 付费账户）
