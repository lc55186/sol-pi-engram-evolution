## Hermes 满配指南 — 分析与改进报告

> 来源：今日头条《全网最细Hermes满配指南：12层架构+2个完整实战+踩坑总结》（2026-09，2.4万字）

---

### 文章核心观点

**12层架构递进路线**（不要跳步）：
```
先跑通 → 再记住你 → 再沉淀技能 → 再接工具 → 再定时运行 → 再多入口触达 → 最后多Agent协同
```

**最佳实践精要**：
- Memory分层：USER.md(我是谁) + MEMORY.md(我在做什么) + Skill(怎么做) + Session(这次发生什么)
- Skill 常驻不超过 5 个，超过说明在用数量代替质量
- MCP allowed_tools 必须白名单，不写=允许所有（高危）
- Cron 只负责"发现和建议"，不负责"擅自改变系统"
- 压缩原则：把具体事件压缩成原则和经验，不堆日期流水账
- 版本控制：~/.hermes/ 目录入 Git，定期提交

---

### 当前系统差距分析

| 层级 | 状态 | 改进项 |
|------|------|--------|
| L1 安装与模型 | ✅ 完成 | v0.21.1 + meituan/longcat-2.0:free |
| L2 输入系统 | ✅ 完成 | SOUL/USER/MEMORY/AGENTS.md 全就位 |
| L3 Memory | ✅ 完成 | 原生记忆运行中，MEMORY.md 92% 需清理 |
| L4 Skills | ✅ 完成 | 24+ 技能，cn-search 已部署 |
| L5 Tools | ⚠️ 部分 | firecrawl keyless 403，需 API Key 或 SearXNG |
| L6 MCP | ⚠️ 刚配置 | GitHub MCP 已写入 config.yaml |
| L7 Gateway | ✅ 完成 | 飞书 WebSocket 运行中 |
| L8 Cron | ✅ 完成 | 4 定时任务（研究/备份/待办/进化） |
| L9 Profiles | ✅ 完成 | researcher + deployer 双 profile |
| L10 可视化 | ⚠️ 部分 | 有 logs 未系统化巡检 |
| L11 Token | ⚠️ 部分 | 有 LoPace 压缩代码，未接入原生配置 |
| L12 多Agent | ✅ 完成 | researcher+deployer+bot-bridge 105轮稳定 |

---

### 已执行的改进

1. **MCP GitHub Server** — 已配置 `allowed_tools` 白名单（search_repositories/get_file_contents/search_issues/search_code）
2. **cn-search Skill** — 国内搜索已部署（百度/搜狗/360/Bing CN 智能路由 + 质量评分）
3. **Hermes 满配指南全文** — 已保存到桌面 `hermes_full_guide_article.txt`（2.4万字）

---

### 剩余待办（按优先级）

| 优先级 | 事项 | 方案 |
|--------|------|------|
| P0 | web_search 后端 403 | 配置 SearXNG 实例 URL 或任一 API Key |
| P1 | Memory 清理压缩 | MEMORY.md 从 92% 压缩到 70% 以下 |
| P1 | Skill 瘦身 | 禁用/合并低频技能，常驻不超 5 个 |
| P2 | 可视化巡检 | 加入 weekly-evolution Cron |
| P2 | Token 监控 | hermes prompt-size 定期检查 |

---

### 文章全文位置

`C:\Users\liuchao\Desktop\hermes_full_guide_article.txt`
