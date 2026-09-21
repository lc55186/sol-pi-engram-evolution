# BOSS-AI-R 经验教训

> 记录日期：2026-09-19

---

## 技术经验

### 环境配置
- paddlepaddle 3.3.1 在 Python 3.11 上运行完美，与 gui-agents 0.3.2 兼容
- 创建 venv 时使用 `uv venv --python 3.11` 确保版本正确
- Windows 下 pip 不在 venv Scripts 目录，需用 `python -m pip`

### Android 开发
- Java 17 (Temurin) 必须放在 PATH 最前面，否则 Java 8 优先导致 sdkmanager 失败
- Gradle wrapper 需要 `gradle-wrapper.properties` 中的 `distributionUrl` 指向国内镜像
- APK 构建命令: `gradle assembleDebug --no-daemon`
- 输出位置: `app/build/outputs/apk/debug/app-debug.apk`

### Hermes 插件系统
- `hermes plugins install` 仅支持 git 仓库 URL，不支持本地路径
- 手动安装：下载 → 解压到 `~/.hermes/plugins/` → `hermes config set web.search_backend wsp`
- 配置文件安全规则：不能直接 patch config.yaml，必须用 `hermes config set`

### Graph 数据库
- 插入数据时需要同时处理 `nodes` + `tasks/events` 两张表
- 关系表需要 `relation_id` 作为主键，建议格式 `rel-{source}-{target}-{counter}`
- 查询时注意 `LEFT JOIN` 和 `WHERE` 条件的顺序影响性能

### 自主待办引擎
- 完成任务后需要创建 `completion event` 和 `next action task` 保持链路完整
- 使用 `json.dumps()` 序列化列表存储在 SQLite TEXT 字段中
- 冷却时间机制防止同一规则重复触发

---

## 产品经验

### BOSS-AI-R 核心场景
- 汽配/体品/再生资源 三行业规则需要分别定制关键词
- P0 预警（账期/质量/担保）必须 <2.5s 延迟
- 决策追溯需要"原声回跳"功能，每条结论必须带证据来源

### 定州试点策略
- 首批 50-80 家目标：高频谈判型老板
- 四级订阅：0/980/6800/29800 元/年
- 月云成本控制：纯云 60-80 元 → 自建 5-15 元

---

## 流程经验

### Git 提交
- Windows 下 git add 时遇到 `nul` 文件需要加 `.gitignore`
- CRLF 警告可忽略，但统一用 LF 更好
- 每次大功能后立即 commit，不要攒到最后

### 测试
- pytest 在 MSYS bash 下运行需要 `python -m pytest` 而不是直接 `pytest`
- 临时数据库用 `tempfile.mktemp()` 创建测试后清理
- 测试函数命名 `test_xxx`，类命名 `TestXxx`

---

*本文件由自主进化引擎自动更新 | 2026-09-19*

---

## 自主待办循环记录

### 循环 #1 — 2026-09-20 09:00
- **执行状态**: ✅ 正常完成
- **待处理任务**: 6 个（无新增）
- **自动完成**: 0 个
  - 原因：P5任务「张总排他代理谈判」未满足自动完成条件（缺少关联 decision 节点）
- **已完成累计**: 6 个
- **数据质量问题**: 「赵总出口订单谈判」存在2条重复记录，建议去重
- **下一步**: 补充张总谈判事件的决策节点以触发自动完成


