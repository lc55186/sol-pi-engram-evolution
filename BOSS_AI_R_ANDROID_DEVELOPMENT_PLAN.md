# BOSS-AI-R Android APK — 分期开发计划

> 创建日期：2026-09-19
> 目标：基于 SoL-Pi × Engram 后端，构建可运行的 BOSS-AI-R Android APK
> 技术栈：Kotlin + Jetpack Compose + WebSocket + Room + ML Kit / 云端 ASR

---

## 项目目录结构

```
C:/Users/liuchao/Desktop/sol-pi-engram-evolution/
├── boss-ai-r-android/              ← Android 工程（Android Studio 项目）
│   ├── app/
│   │   ├── src/main/
│   │   │   ├── java/com/bossair/app/
│   │   │   │   ├── MainActivity.kt
│   │   │   │   ├── BossAIApp.kt
│   │   │   │   ├── di/
│   │   │   │   │   └── AppModule.kt
│   │   │   │   ├── data/
│   │   │   │   │   ├── api/         ← Retrofit API 接口
│   │   │   │   │   ├── ws/          ← WebSocket 客户端
│   │   │   │   │   ├── db/          ← Room 数据库
│   │   │   │   │   └── repo/        ← 仓库层
│   │   │   │   ├── domain/
│   │   │   │   │   ├── model/       ← 数据模型
│   │   │   │   │   └── usecase/     ← 用例
│   │   │   │   ├── service/
│   │   │   │   │   ├── AudioRecordService.kt  ← 前台录音服务
│   │   │   │   │   └── WebSocketService.kt
│   │   │   │   └── ui/
│   │   │   │       ├── theme/
│   │   │   │       ├── screens/
│   │   │   │       └── components/
│   │   │   ├── res/
│   │   │   └── AndroidManifest.xml
│   │   └── build.gradle.kts
│   └── build.gradle.kts
├── sol_pi_engram_evolution/        ← 后端（已有）
└── BOSS_AI_R_PRD_DETAILED.md       ← PRD 文档
```

---

## 分期开发计划

### Phase 0: 工程脚手架（1-2 天）
**目标**：Android 项目可编译运行，显示 "Hello BOSS-AI-R"

**产出**：
- Android Studio 工程骨架
- Jetpack Compose 主题（深色商务风）
- 底部导航（实时副驾 / 经营外脑 / 知识图谱 / 设置）
- Hilt 依赖注入配置
- 基础 CI/CD（GitHub Actions 构建 APK）

**验收**：
- `./gradlew assembleDebug` 成功生成 APK
- 安装到手机/模拟器可启动

---

### Phase 1: 实时录音 + 三重合规指示（2-3 天）
**目标**：录音功能可用，合规三重指示完整

**产出**：
- `AudioRecordService`：前台服务录音，保活
- 三重指示：应用内红色脉冲 + 系统级指示 + 常驻通知
- 场景选择器（商务谈判/办公会议/公开用餐/私密聚会/他人场所）
- 录音状态机（待机 → 录音中 → 暂停 → 会后处理）

**验收**：
- 点击开始录音，通知栏常驻通知出现
- 录音可后台持续 ≥1 小时
- 来电暂停、挂断续录

---

### Phase 2: 实时转写 + WebSocket 通信（2-3 天）
**目标**：音频实时上传，ASR 结果实时显示

**产出**：
- WebSocket 客户端（OkHttp）
- 音频分帧上传（PCM → 编码 → WebSocket 二进制帧）
- 滚动字幕 UI（说话人标签 + 时间戳）
- 流式 ASR 输出展示
- 自动重连机制

**验收**：
- 录音中实时显示转写文字
- 断网自动重连
- 网络切换（WiFi→4G）不中断

---

### Phase 3: 关键词预警 + 耳语提示（2-3 天）
**目标**：识别关键信息并震动提醒

**产出**：
- 关键词规则引擎（汽配/体品/再生资源 三行业）
- 提示决策器（去重/分级/择时）
- 震动模式编码（短震=注意、长震=风险、双震=商机）
- 锁屏大字提示
- 通知栏富媒体提示

**验收**：
- 对方说"60天账期"时触发震动
- 提示延迟 <2.5s
- 同一关键词 30s 内不重复提醒

---

### Phase 4: 会后五件套生成（2-3 天）
**目标**：结束录音后自动生成结构化纪要

**产出**：
- 五件套 API 调用（纪要/商机/待办/决策卡/复盘）
- 会后结构化页面展示
- 原声回跳（点击文字跳转音频时间点）
- 分享/导出功能

**验收**：
- 结束录音后 30s 内生成纪要
- 每条商机/待办可点击跳转原声
- 可复制/分享

---

### Phase 5: 经营外脑 + 双向融合（2-3 天）
**目标**：昨日谈判数据汇入经营日报

**产出**：
- 今日必盯 3 件事（推送/首页卡片）
- 昨日谈判捕获列表
- 经营统计卡片（营收/毛利/应收/谈判次数）
- 双向融合闭环流程图

**验收**：
- 每日 8:00 自动推送 3 件事
- 谈判数据会后 5 分钟内写入经营库
- 经营数据可注入实时提示

---

### Phase 6: 知识图谱 + 用户系统（2-3 天）
**目标**：谈判数据可视化，用户注册登录

**产出**：
- 知识图谱可视化（Canvas 绘制节点关系）
- 手机号注册/登录
- 声纹注册（10 秒录音）
- 四级订阅 UI（L0/L1/L2/L3）

**验收**：
- 图谱正确渲染客户/谈判/商机节点
- 注册登录流程完整
- 声纹注册成功

---

### Phase 7: 集成测试 + APK 打包（1-2 天）
**目标**：端到端流程跑通，生成可安装 APK

**产出**：
- 端到端测试（注册→录音→转写→提示→纪要）
- ProGuard 混淆配置
- 签名 APK 生成
- 内测分发（Firebase App Distribution / 蒲公英）

**验收**：
- 完整流程无崩溃
- APK 可安装到 Android 8+ 设备
- 启动时间 <2s

---

## 时间估算

| Phase | 工作量 | 依赖 |
|-------|--------|------|
| Phase 0 | 1-2 天 | Android SDK |
| Phase 1 | 2-3 天 | Phase 0 |
| Phase 2 | 2-3 天 | Phase 1 |
| Phase 3 | 2-3 天 | Phase 2 |
| Phase 4 | 2-3 天 | Phase 2 |
| Phase 5 | 2-3 天 | Phase 4 |
| Phase 6 | 2-3 天 | Phase 0 |
| Phase 7 | 1-2 天 | Phase 3,4,5,6 |
| **总计** | **14-22 天** | |

---

## 当前环境检查

需要确认：
1. Android SDK 是否安装
2. Android Studio 是否可用
3. JDK 版本（需要 JDK 17+）
4. 模拟器或真机调试环境

---

*V1.0 | 2026-09-19*
