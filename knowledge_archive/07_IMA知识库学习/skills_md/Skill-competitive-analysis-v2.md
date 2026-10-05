# Skill-competitive-analysis-v2

***

name: competitive-analysis
description: 开源项目竞品技术深度分析。当用户要求分析一个开源/GitHub项目，并与自有项目做技术对比时触发。触发词：竞品分析 / 对比分析 / 技术对比 / 深挖 / 看看这个项目 / 和我们的比怎么样 / 开源项目分析 / 技术调研 / GitHub Trending 分析。
category: development
tags: \[竞品分析, GitHub, 技术对比, 开源项目]
---------------------------------

# Competitive Analysis — 开源项目竞品技术分析

## When to Use

* 用户给出一个 GitHub 仓库链接或项目名，要求分析技术细节
* 用户要求将外部项目与自有项目做技术对比
* 用户说"深挖"、"看看这个项目怎么样"、"和我们的比一下"
* GitHub Trending 项目技术评估
* 用户粘贴一段关于某项目的宣传文章，要求验证真实性

## Procedure

### Step 1: 获取外部项目数据

**优先级顺序（能 MRP 就用 MRP，别浪费 curl）：**

```bash
# A. MCP 工具优先（无需 auth/config）
mcp__github__search_repositories → mcp__github__get_file_contents → mcp__github__list_commits

# B. 备选：REST API（需 --noproxy "*"，否则代理路径 404）
curl -sL --noproxy "*" "https://api.github.com/repos/{owner}/{repo}" | jq '{stars: .stargazers_count, forks: .forks_count, license: .license.spdx_id, updated: .updated_at}'

# C. README/文档：web_extract（比 base64 decode 快）
web_extract(urls=["https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"])

# D. 大段文档：web_extract char_limit=15000（超出部分存磁盘，read_file 翻页）
```

**Git 元信息：**

```bash
# 克隆后快速画像
git clone https://github.com/{owner}/{repo} /tmp/wt-analysis-{repo}
git -C /tmp/wt-analysis-{repo} log --oneline --all | wc -l  # 总提交数
git -C /tmp/wt-analysis-{repo} log --oneline -30             # 最近动态
git -C /tmp/wt-analysis-{repo} branch -a                     # 分支结构
git -C /tmp/wt-analysis-{repo} log --oneline --all --format="%ad %s" --date=short | head -30  # 时间线
```

**并行策略：** 搜索、文件内容、日志统计全部并发调用，不要串行等待。

### Step 1.5: 文档深度扫描

```bash
# 发现 docs/research/ADR 等深度内容
curl -sL --noproxy "*" "https://api.github.com/repos/{owner}/{repo}/contents/docs" | python3 -c "import json,sys; d=json.load(sys.stdin); [print(f'{i[\"name\"]}: {i[\"size\"]} bytes') for i in d if i.get('type')=='file']"
```

**关键限制：**

* 未认证 rate limit: 60/小时；认证: 5000/小时
* 429 错误 sleep 50-60 秒后重试
* 大文件用 web\_extract（char\_limit）而不是 base64 全文拉取

### Step 2: 分析本地项目

```bash
# 代码行数统计
find <project-dir> -name "*.py" -o -name "*.rs" -o -name "*.ts" | xargs wc -l

# 技术栈识别
ls -la *.toml *.json requirements.txt
```

### Step 3: 生成结构化对比

按以下维度生成对比表：

| **维度** | **外部项目**           | **自有项目** |
| ------ | ------------------ | -------- |
| 代码规模   | LOC / 文件数 / 测试行数   | ...      |
| 技术栈    | 语言 + 关键依赖 + 版本     | ...      |
| 核心架构   | 分层设计 + 关键机制        | ...      |
| 功能覆盖   | 已实现 vs 待实现         | ...      |
| 性能指标   | 延迟/吞吐/资源占用         | ...      |
| 生态集成   | MCP/Plugin/Skill 等 | ...      |
| 部署方式   | 二进制/容器/源码          | ...      |
| 测试覆盖   | 测试文件数 + 覆盖率        | ...      |
| 安全机制   | 权限/沙箱/审计           | ...      |
| 社区活跃度  | 提交频率/PR处理/issue响应  | ...      |
| 治理机制   | 版本控制/变更流程          | ...      |

### Step 4: 输出可行动建议

必须包含：

1. **值得借鉴的点**（有明确落地价值的特性）
2. **不建议照搬的部分**（过度工程/不匹配场景）
3. **建议行动项**（按优先级排序，含工作量估计）

## Pitfalls

* **不要只看 README 宣传** — 必须验证实际代码结构和 API 返回数据
* **不要忽略许可证** — 对比时注意开源协议兼容性（MIT/Apache vs GPL）
* **不要只列差异** — 必须给出"so what"，对自有项目的具体价值
* **不要夸大外部项目** — 基于代码事实，不基于 marketing 话术
* **MCP 优先于 curl** — 能走 MRP 工具就不要手动拼 REST URL
* **并行调用独立数据** — repo 搜索、文件内容、日志统计全部并发
* **大文档用 web\_extract** — 别 base64 拉全文，char\_limit=15000 自动分页

## 案例：Reasonix 分析（2026-08-02）

项目：esengine/DeepSeek-Reasonix

核心创新：双模型协作（Planner+Executor）、上下文三级压缩、MCP 插件层

Hermes 借鉴点：

* P0：上下文压缩策略（60%/80%/90%）
* P1：记忆自动注入（BM25 检索相关事实）
* P2：双会话隔离（保护前缀缓存）

详见：`references/reasonix-analysis-2026-08-02.md`

## 步骤

1. **准备输入** — 确认输入数据和参数完整
2. **执行处理** — 调用工具完成核心逻辑
3. **输出结果** — 生成目标产物（文件/报告/状态）
4. **异常处理** — 失败时返回错误信息，不静默

## 验证

- [ ] 输出文件/报告已生成

- [ ] 处理逻辑覆盖主要场景

- [ ] 错误情况有明确提示

- [ ] 输出格式符合预期
