# Skill-agent-reach

***

name: agent-reach
description: >-
Agent Reach 全网信息检索。通过 CLI 覆盖 17 平台：全网语义搜索(Exa)、Jina Reader、
GitHub、YouTube/Bilibili/抖音、Reddit、V2EX、Twitter/X、微信公众号、RSS、LinkedIn。
零 API Key 费用，7 渠道即装即用。
触发词：社交媒体搜索、竞品分析、热点追踪、视频内容提取、GitHub 搜索、B站搜索、
Reddit 讨论、V2EX 话题、微信公众号、RSS 订阅、全网搜索、网页内容提取、抖音解析、
Twitter 推文、YouTube 字幕、LinkedIn 招聘。
triggers: 社交媒体搜索、竞品分析、热点追踪、视频信息提取、GitHub 搜索、B站搜索、Reddit 讨论、V2EX 话题、微信公众号、RSS 订阅、全网搜索、网页内容提取、抖音解析、Twitter推文、YouTube字幕、LinkedIn招聘
-------------------------------------------------------------------------------------------------------------------------------

# Agent Reach 全网检索路由器

17 平台工具集合，补充 Hermes 原生 `web_search` 的不足。

## 路由表

| **用户意图**                    | **分类** | **详细文档**                                     |
| --------------------------- | ------ | -------------------------------------------- |
| 网页搜索/代码搜索                   | search | [references/search.md](references/search.md) |
| 小红书/抖音/微博/推特/B站/V2EX/Reddit | social | [references/social.md](references/social.md) |
| 招聘/职位/LinkedIn              | career | [references/career.md](references/career.md) |
| GitHub/代码                   | dev    | [references/dev.md](references/dev.md)       |
| 网页/文章/公众号/RSS               | web    | [references/web.md](references/web.md)       |
| YouTube/B站/播客字幕             | video  | [references/video.md](references/video.md)   |

## 推荐调用方式

**统一入口脚本**（无需激活 venv）：

```bash
bash scripts/agent-reach.sh <command> [args...]
```

## 快速调用

```bash
# === 搜索 & 网页 ===
bash scripts/agent-reach.sh search "关键词" [n]          # 全网语义搜索 (Exa)
bash scripts/agent-reach.sh fetch <url>                 # 网页内容提取 (Exa)
bash scripts/agent-reach.sh jina <url>                  # 任意网页提取 (Jina Reader)

# === GitHub ===
bash scripts/agent-reach.sh github search "query"      # GitHub 仓库搜索
bash scripts/agent-reach.sh github issues "query"      # GitHub Issues
bash scripts/agent-reach.sh github view owner/repo   # GitHub 仓库详情

# === 视频平台 ===
bash scripts/agent-reach.sh youtube <url>               # YouTube 视频信息
bash scripts/agent-reach.sh youtube_sub <url>           # YouTube 字幕提取
bash scripts/agent-reach.sh bili search "query"        # Bilibili 搜索
bash scripts/agent-reach.sh bili hot                   # Bilibili 热门
bash scripts/agent-reach.sh bili rank                  # Bilibili 排行榜
bash scripts/agent-reach.sh bili video <bvid>          # Bilibili 视频详情
bash scripts/agent-reach.sh bili user <uid>            # Bilibili UP主信息
bash scripts/agent-reach.sh bili sub <url>             # Bilibili 字幕提取
bash scripts/agent-reach.sh douyin <share_link>        # 抖音视频解析

# === Reddit ===
bash scripts/agent-reach.sh reddit search "query"      # Reddit 搜索
bash scripts/agent-reach.sh reddit read <id>           # Reddit 帖子详情
bash scripts/agent-reach.sh reddit sub <name>          # Reddit 子版块
bash scripts/agent-reach.sh reddit popular             # Reddit 热门
bash scripts/agent-reach.sh reddit status              # Reddit 登录状态

# === V2EX (公开 API，无需认证) ===
bash scripts/agent-reach.sh v2ex hot                   # V2EX 热门主题
bash scripts/agent-reach.sh v2ex node <name>           # V2EX 节点主题 (python/tech/jobs/...)
bash scripts/agent-reach.sh v2ex topic <id>            # V2EX 主题详情
bash scripts/agent-reach.sh v2ex replies <id>          # V2EX 主题回复
bash scripts/agent-reach.sh v2ex user <name>           # V2EX 用户信息

# === Twitter/X ===
bash scripts/agent-reach.sh twitter feed               # Twitter 首页时间线
bash scripts/agent-reach.sh twitter tweet <url>        # 单条推文详情
bash scripts/agent-reach.sh twitter user-posts <user>   # 用户时间线

# === 内容 ===
bash scripts/agent-reach.sh wechat "query"             # 微信公众号搜索
bash scripts/agent-reach.sh rss <feed_url>             # RSS/Atom 订阅源

# === 状态 ===
bash scripts/agent-reach.sh doctor                      # 检查所有渠道状态
```

## 直接调用（需要激活 venv）

```bash
source ~/.agent-reach-venv/bin/activate
```

### Exa 搜索 (MCP)

```bash
mcporter call exa.web_search_exa --query "query" --numResults 5 --output text
mcporter call exa.web_fetch_exa --urls '["https://example.com"]' --maxCharacters 5000 --output text
mcporter call exa.get_code_context_exa --query "code question" --tokensNum 3000 --output text
```

### yt-dlp (YouTube/B站字幕)

```bash
# YouTube 字幕
yt-dlp --write-auto-sub --sub-lang "zh-Hans,zh,en" --skip-download -o "/tmp/%(id)s" "URL"

# B站字幕
yt-dlp --write-sub --write-auto-sub --sub-lang "zh-Hans,zh,en" --convert-subs vtt --skip-download -o "/tmp/%(id)s" "URL"

# 搜索
yt-dlp --dump-json "ytsearch5:query"
```

### feedparser (RSS)

```python
python3 -c "
import feedparser
for e in feedparser.parse('FEED_URL').entries[:5]:
    print(f'{e.title} — {e.link}')
"
```

## 渠道状态 (2026-06-17)

| **渠道**      | **状态** | **认证**   | **说明**                                                |
| ----------- | ------ | -------- | ----------------------------------------------------- |
| GitHub      | ✅      | gh CLI   | 搜索/Issue/PR/仓库                                        |
| YouTube     | ✅      | 无需       | 视频信息+字幕提取                                             |
| Reddit      | ⚠️     | 部分需登录    | 搜索可用，feed/save 需 `rdt login`                          |
| Exa 全网搜索    | ❌      | 免费额度     | **当前 VPS 上 `mcporter: Unknown MCP server 'exa'`，不可用** |
| Jina Reader | ❌      | 无需       | **当前 VPS 上 timeout (exit 28)，不可用**                    |
| V2EX        | ✅      | 无需       | 公开 API，热门/节点/详情/回复                                    |
| Exa 全网搜索    | ❌      | 免费额度     | **当前 VPS 上 `mcporter: Unknown MCP server 'exa'`，不可用** |
| Jina Reader | ❌      | 无需       | **当前 VPS 上 timeout (exit 28)，不可用**                    |
| Twitter/X   | ⚠️     | 需 Cookie | 可用但 VPS IP 有封号风险                                      |
| 抖音          | ⚠️     | 需 MCP    | douyin-mcp-server 需安装                                 |
| 微信公众号       | ✅      | 免费额度     | 通过 Exa 搜索                                             |
| 微博          | ⚠️     | 网页抓取     | Jina Reader 读取                                        |
| 小红书         | ❌      | 需 Cookie | xhs                                                   |
