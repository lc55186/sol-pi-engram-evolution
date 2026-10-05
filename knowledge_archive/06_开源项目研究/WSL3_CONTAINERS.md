# WSL 3.0 研究分析报告（Windows 原生 Linux 容器）

> 生成时间：2026-10-03
> 来源：头条「幸运」《微软突然放大招：WSL3.0来了》+ 官方交叉验证
> 官方依据：blogs.windows.com（2026-09-29，Logan Iyer CV 署名）GA 公告 + Microsoft Learn `wsl-container` 文档
> 结论先行：**WSL 3.0.1 引擎已于 2026-09-29 正式 GA，核心是 WSL 容器能力（wslc）——Windows 11 原生跑 Linux 容器，不再依赖 Docker Desktop。**

## 一、官方事实核对（非头条转述）

| 头条说法 | 官方核实 |
|---------|---------|
| WSL 3.0 支持 Linux 容器 | ✅ **WSL containers 于 2026-09-29 GA**（非"3.0"命名，引擎版本号 3.0.1.0） |
| wslc 工具 | ✅ `wslc.exe` 随 WSL ≥2.9.3 内置（GA 版完整），别名 `container.exe`，命令风格兼容 docker（build/run/ps/cp/restart…） |
| Windows 程序可调用容器 API | ✅ `Microsoft.WSL.Containers` NuGet 包（C#/C++/WinRT 投影），三对象模型：WslcService / Session / Container |
| consomme 网络模式 | ✅ 容器流量经 Windows 主机转发，兼容代理/企业网络策略 |
| Linux 6.18 内核 | ✅ 本机 WSL 内核已报 6.18.33.2 |
| virtiofs 文件访问翻倍 | ✅ 官方称 Linux 侧访问 Windows 文件最高 2x 提速（wslc 场景） |
| MIT 开源命令行/服务 | ✅ WSL 命令行工具、后台服务、容器启动组件、WSLg 图形堆栈以 MIT 开源（GitHub microsoft/wsl） |
| 工具链全覆盖（创建/启动/停止/导出/检查/清理、CPU内存限制、GPU 访问） | ✅ GA 新增：restart、cp、system info、network connect/disconnect/create（支持任意驱动选项）、events 实时流、健康检查、--stop-timeout、--mount、可配置存储路径 |
| 企业管控 | ✅ Intune 可开关容器能力、限制镜像拉取来源；Defender for Endpoint 插件覆盖容器进程/文件/网络活动并关联回 Windows 宿主 |

## 二、架构定位

- **和 Docker Desktop 的关系**：竞争而非替代关系。Docker 要起一个 Linux VM 引擎（Hyper-V/WSL2）+ 守护进程；wslc 直接跑在 WSL 引擎里，**零额外 VM、零 Docker 依赖**。二者可共存（本机现状：Docker Desktop 在跑 + WSL 引擎 2.7）。
- **和 Cua Fleets 的关系**：Cua 的"云桌面舰队"要按秒付费；wslc 是本机免费容器层，适合本地开发/AI 沙箱。
- **Session 0 / 服务场景**：wslc 引擎在用户会话里；服务会话（Hermes 跑的地方）可调用 wslc 容器，但引擎升级/首次安装需提权。

## 三、本机实测（2026-10-03）

| 项 | 结果 |
|----|------|
| 虚拟化 | ✅ Intel i7-10610U，VirtualizationFirmwareEnabled=True |
| WSL 引擎 | 2.7.14.0（**旧**，wslc 未内置） |
| WSL 内核 | 6.18.33.2（已是 6.18 系） |
| wslc 命令 | ❌ 不在 PATH（引擎太旧） |
| `wsl --update` | ⚠️ 已自动下载 `wsl.3.0.1.0.x64.msi`（367MB）到 Temp，**安装失败：0x80070065（需管理员）** —— Session 0 服务会话无提权通道 |

**解锁方案（已备好，待你双击）**：`C:/Users/liuchao/Desktop/WSL3-安装wslc.bat`
- 自动请求 UAC 提权 → `wsl --update` 安装 3.0.1 引擎 → `wsl --shutdown` 重启 → 验证 `wsl --version` + `where wslc`
- 装好后 wslc 直接可用（无需重启 Windows）

**装好后立即可验的三条命令**：
```
wslc run --rm -it mcr.microsoft.com/cFSM/cowsay "hello"   # 官方 cowsay 冒烟
wslc container ps
wslc system info
```

## 四、对本项目的价值判断

1. **解掉 Cua Bench 容器层的老大难**：Cua（trycua）默认 gVisor 容器 backend 在 Windows 上跑不了；Docker Desktop 又锁在交互式会话（Hermes 服务会话里 socket Access is denied）。**wslc 引擎随 Windows 原生注册，服务会话可直连** —— Cua Bench 若支持自定义 backend 或 docker-compatible 引擎接入，wslc 是最省事的本地容器层（至少能先让完整 agent 任务闭环在 Windows 上跑起来）。
2. **AI 本地沙箱场景**：WSL container API 官方点名"运行本地 AI workloads"——SO 4/SO 4 场景下给 agent 开隔离 Linux 沙箱（跑不信任代码、端到端测试），不用再养 Docker Desktop 那台 VM，资源占用更低。
3. **BOSS-AI-R / RK3588 线**：端侧盒子是 ARM，wslc 是 x86/Win11 特性，**不直接相关**；但"容器即沙箱、API 即接口"的设计范式对端侧 agent 隔离执行模块有参照意义（RK3588 侧对应方案是 LXC/Aegiscontainer）。
4. **Hermes 生态**：每日 IMA 备份等 cron 任务若将来需要 Linux 环境依赖（比如 cos 签名工具链），wslc 比 Docker 轻。

## 五、开发者社区反应（搜自 Reddit/windowslatest/windowscentral）

- 普遍正面：「终于少做了一步」「不用装虚拟化软件了」「Intune/Defender 管控是落地关键」。
- 关注点：Compose 支持还在 roadmap（GA 暂无）；`container.exe` 别名降低了从 docker 迁移的心理成本。

## 六、待办

- [ ] 双击 `WSL3-安装wslc.bat` 完成引擎升级（需 UAC 管理员）
- [ ] 升级后跑 `wslc run cowsay` 冒烟 + `wslc system info` 留档
- [ ] 评估 Cua Bench 接 wslc backend 的可行性（看 cua-bench 是否支持 docker socket 类配置）
- [ ] （可选）C# 小脚本调 `Microsoft.WSL.Containers` NuGet 验证 API 编程面

---

# 附录：wslc 本机实测验证（2026-10-03 完成）

> 环境：Windows 11 (10.0.26100.9457) x86_64
> 结论：**WSL 引擎已升级到 3.0.1.0，wslc 容器引擎全链路实测通过（真实拉镜像 + 运行 + exec + 生命周期管理）**

## A1. 升级过程：三次失败 → 成功

| 尝试 | 方式 | 结果 | 根因 |
|------|------|------|------|
| v1~v3 | `.bat` 里跑 `wsl --update` | 引擎停在 2.7.14.0 | **`wsl --update` 走交互式 MSI UI，服务会话（Session 0）无人确认 → MSI 返回 1602（用户取消）→ 自动回滚** |
| v4 | 静默装 MSI | 用户改在**管理员 PowerShell** 直接 `wsl --update` 成功 | 关键差异：真实交互式管理员终端，UAC 可被点确认 |

**教训（重要）**：`wsl --update` 必须由用户在交互式管理员终端执行；Hermes 所在的 Session 0 服务会话执行会静默失败（1602）。
替代路径：在交互式会话里 `msiexec /i wsl.3.0.1.0.x64.msi /qn` 静默安装。

升级后版本：
```
WSL 版本: 3.0.1.0
内核版本: 6.18.40.1-1
WSLg 版本: 1.0.79
```
`wslc.exe` / `wslcsession.exe` / `container.exe` 位于 `C:\Program Files\WSL\`（**默认不在 PATH**，需手动加）。

## A2. 全链路实测（全部真实执行，无 mock）

| 测试 | 命令 | 结果 |
|------|------|------|
| 版本 | `wslc version` | ✅ `wslc 3.0.1.0` |
| 引擎信息 | `wslc info` | ✅ 客户端 3.0.1.0 / 服务端会话管理器 3.0.1 |
| 拉镜像+运行 | `wslc run <mirror>/library/alpine echo wslc-works` | ✅ 输出 `wslc-works` |
| 后台长驻 | `wslc run -d --name t1 ... sleep 300` | ✅ 返回容器 ID |
| 容器列表 | `wslc list` | ✅ `Up Less than a second` |
| 容器内执行 | `wslc exec t1 uname -a` | ✅ `Linux ... 6.18.40.1-microsoft-standard-WSL2 x86_64` |
| 容器内写文件 | `wslc exec t1 sh -c "echo ... > /tmp/x.txt && wc -l"` | ✅ `1 /tmp/x.txt` |
| 停止/删除 | `wslc stop t1` / `wslc rm t1` | ✅ 均 rc=0 |
| 历史列表 | `wslc list -a` | ✅ 正确显示 Exited 容器 |

**关键证据**：容器内 `uname -a` = **6.18.40.1-microsoft-standard-WSL2**，与宿主 WSL 内核一致
→ 证明是**原生 WSL 引擎容器**（无额外 VM、无 Docker 依赖），这正是 wslc 的核心价值。

## A3. 关键坑：国内拉不到镜像

**症状**：
```
Get "https://registry-1.docker.io/v2/": context deadline exceeded → E_FAIL
```

**根因**：**wslc 目前不支持 registry mirror 配置**（microsoft/WSL #40951，3.0.1.0 仍 open）。
`settings.yaml` 只有 session CPU/内存选项。

**官方变通方案（实测有效）**：镜像名里直接写镜像主机前缀
```bash
wslc run docker.m.daocloud.io/library/alpine:latest echo wslc-works   # ✅ 8.8s 成功
```
其他可用源：`docker.1ms.run`、`docker.1panel.live`。
终极备选（所有 registry 不通时）：`docker save x.tar` → `wslc load -i x.tar`。

## A4. 已知限制

- [ ] wslc 无 registry mirror 配置（等 Microsoft 实现 #40951）
- [ ] 不支持 credential helper（#41030）、跨 registry push（#41040）
- [ ] 仅 x86/Win11 —— **不能直接用于 RK3588 端侧**（端侧另走 LXC 方案）
- [ ] 已写入用户 PATH，**需重开终端生效**

## A5. 对本项目的意义

1. **本机开发沙箱**：零 Docker 依赖的轻量 Linux 容器，绕开此前 Docker Desktop 的 Session 0 限制
2. **Cua Bench 可能性**：Cua Bench 此前因 gVisor 无 Windows 支持 + Docker Session 0 限制走不通；
   wslc 是原生 WSL 引擎容器，**可能成为 Cua Bench 可用后端**（待验证）
3. **端侧架构参照**：wslc 的"原生引擎容器、无额外 VM"思路，与 RK3588 端侧轻量容器化方向一致
