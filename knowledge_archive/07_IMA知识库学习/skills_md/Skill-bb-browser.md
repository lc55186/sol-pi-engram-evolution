# Skill-bb-browser

***

name: bb-browser
description: "把真实 Chrome 浏览器变成 AI 可操控的 API。通过 CDP 接管已登录的浏览器， 让 AI 直接用你的登录态操作网页——点击、填表、读取、截图。 触发词：操作网页 / 登录某网站 / 抓取需要登录的页面 / 自动化浏览器 / 浏览器操作 / bb-browser。 适用：需要登录态的网页操作、反爬场景、无 API 的网站自动化、结构化数据提取。 反例：大规模批量爬取（用 Scrapy）、无登录需求的简单抓取（用 web\_extract）。"
version: 1.0.0
--------------

# bb-browser — 你的浏览器就是 API

## 核心概念

bb-browser 通过 Chrome DevTools Protocol (CDP) 接管你**正在使用的 Chrome 浏览器**，让 AI Agent 用你的真实登录态（Cookie、User-Agent、TLS 指纹）操作网页。

**不是爬虫，不是 headless 浏览器——是"借你的身份上网"。**

## 安装

```bash
npm install -g bb-browser
bb-browser site update  # 更新社区适配器
```

## 架构

```
AI Agent → bb-browser CLI ──HTTP──▶ Daemon (127.0.0.1:19824) ──CDP WebSocket──▶ 你的 Chrome
```

## 快速上手

### 启动 Daemon

```bash
bb-browser  # 默认绑定 127.0.0.1:19824
```

### 基本操作

```bash
# 打开网页
bb-browser open https://example.com

# 获取可访问性树快照（-i = interactive，只返回可交互元素）
bb-browser snapshot -i

# 点击元素（ref 从 snapshot 获取）
bb-browser click @3

# 填写输入框
bb-browser fill @5 "hello"

# 执行 JavaScript
bb-browser eval "document.title"

# 截图
bb-browser screenshot

# 认证态 fetch（用当前页面的 Cookie/登录态请求 API）
bb-browser fetch https://api.example.com/data --json

# 查看当前 daemon 状态
bb-browser status

# 查看所有可用适配器
bb-browser site list

# 搜索适配器
bb-browser site search github
```

### 结构化输出

所有命令支持 `--json` + `--jq`：

```bash
# 获取知乎热榜前5
bb-browser site zhihu/hot 5 --json

# 过滤字段
bb-browser site xueqiu/hot-stock 5 --jq '.items[] | {name, changePercent}'
```

### 社区适配器（145 个）

覆盖 36 平台：Google/Baidu/Bing/DDG/Sogou | Twitter/Reddit/微博/小红书/LinkedIn | 36kr/头条 | GitHub/StackOverflow/HN/npm/PyPI/arXiv | YouTube/B站 | 雪球/Yahoo Finance | BOSS直聘 | Wikipedia/知乎 | 什么值得买 | 有道/Product Hunt/携程

### 自定义适配器

让 AI 自动把任意网站变成 CLI 命令：

```bash
# 1. 逆向分析网站 API
bb-browser network --with-body https://example.com

# 2. AI 根据网络请求编写适配器
# 3. 测试并提交到 bb-sites 仓库
```

复杂度等级：

* **L1（\~1min）**：Cookie 直接 fetch（Reddit/GitHub）
* **L2（\~3min）**：Bearer + CSRF Token（Twitter/知乎）
* **L3（\~10min）**：Webpack 注入/Pinia store（Twitter 搜索/小红书）

## MCP Server 集成

作为 MCP Server 接入 Claude Code/Cursor/Hermes：

```json
{
  "mcpServers": {
    "bb-browser": {
      "command": "npx",
      "args": ["-y", "bb-browser", "--mcp"]
    }
  }
}
```

## 参考

* **完整适配器列表 + 复杂度等级**：`references/bb-browser-adapters.md`（36 平台、L1-L3 分级）

## Procedure

### 当用户要求操作需要登录的网页时

1. **确认 Chrome 已启动并登录目标网站**
2. **启动 bb-browser daemon**（如未运行）：`bb-browser &`
3. **使用适配器或基本操作完成任务**：
   * 有适配器：`bb-browser site <platform>/<action> --json`
   * 无适配器：`bb-browser open <url> && bb-browser snapshot -i` → 解析快照 → 执行操作
4. **返回结构化结果给用户**

### 当用户要求抓取需要登录的数据时

1. 检查是否有对应适配器：`bb-browser site list | grep <platform>`
2. 有适配器：直接调用 `bb-browser site <platform>/<action> --json --jq <filter>`
3. 无适配器：用 `bb-browser open` + `bb-browser eval` 提取数据

### 当用户要求自动化浏览器操作时

1. `bb-browser open <url>` 打开目标页面
2. `bb-browser snapshot -i` 获取元素快照
3. 根据元素 ref 执行 `bb-browser click`/`bb-browser fill`/`bb-browser press`
4. 用 `bb-browser eval` 验证操作结果

## Verification

* **Verdict**: 操作完成后截图或快照验证结果
* **Next Step**: 返回结构化数据或截图给用户确认

## Pitfalls

* **安全红线**：bb-browser 绑定 127.0.0.1，绝不暴露公网。绑定 0.0.0.0 = 向全网敞开浏览器
* **风控约束**：使用真实账号，高频操作会被平台风控
* **不适场景**：大规模批量爬取（用 Scrapy）、无登录需求（用 web\_extract）
* **适配器质量**：社区维护，部分适配器可能因网站更新失效
* **Chrome 依赖**：需要 Chrome 运行中，且已启用远程调试端口。针对不同环境的注意事项：
  * **Linux 服务器（RHEL/CentOS/Amazon Linux）**：Chromium 通过 EPEL 仓库安装时，二进制名是 `chromium-browser`，不是 `google-chrome`；需以无头模式启动时，添加 `--no-sandbox` 规避权限限制
  * **bb-browser 连接失败**：若报错无法找到浏览器，需确认：1）Chrome/Chromium 已启动远程调试端口（`--remote-debugging-port=9222`）；2）通过环境变量 `BB_BROWSER_CDP_URL=http://localhost:9222` 绑定到该端口
* **json 输出**：部分适配器不支持 `--json`，需要先不加 `--json` 跑一次看原始输出，再决定如何解析。遇到 `error: unknown option: --json` 时，改用 `bb-browser site <platform>/<action> 2>&1` 然后手动提取
* **适配器失效**：社区适配器可能因网站更新失效。失效时用 `bb-browser network --with-body <url>` 逆向分析，重新编写。参考 `references/bb-browser-adapters.md` 查看复杂度等级

## 安全加固

* 绑定白名单域名（只允许操作指定网站）
* 禁止在 bb-browser 中输入密码/支付操作
* 敏感操作需用户确认
* 日志记录所有 bb-browser 操作

## 步骤

1. **接收输入** — 确认输入参数和上下文
2. **执行处理** — 完成核心任务
3. **返回结果** — 输出处理结果

## 验证

- [ ] 任务目标已达成

- [ ] 输出格式正确

- [ ] 错误情况已处理
