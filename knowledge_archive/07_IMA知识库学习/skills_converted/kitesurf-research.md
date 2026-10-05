---
name: kitesurf-research
description: 研究 Kitesurf（Cloudflare AI Agent 专用浏览器）
version: 1.0.0
category: research
tags: ["kitesurf", "browser", "research", "cloudflare"]
metadata:
  hermes:
    tags: ["kitesurf", "browser", "research", "cloudflare"]
    source: IMA 知识库导入
---

# kitesurf-research

> 研究 Kitesurf（Cloudflare AI Agent 专用浏览器）。当用户询问/研究/评估 Kitesurf 或 AI Agent 专用浏览器时激活。触发词：Kitesurf / AI 专用浏览器 / Cloudflare 浏览器 / 无状态浏览器。

# Kitesurf Research — Cloudflare AI Agent 浏览器

## When to Use

* 用户询问 Kitesurf 浏览器能力
* 评估 AI Agent 专用浏览器方案
* 对比 Kitesurf vs Puppeteer/Playwright vs Chromium
* 研究无状态浏览器架构

## Procedure

1. **搜索 GitHub**（备用方案，因搜索服务常不可用）：

```bash
curl -sL --noproxy '*' --connect-timeout 10 --max-time 20 \
  'https://api.github.com/search/repositories?q=kitesurf+AI+agent+browser&sort=stars&order=desc&per_page=10'
```

2. **读取 README**（官方文档）：

```bash
curl -sL --noproxy '*' --connect-timeout 10 --max-time 20 \
  'https://api.github.com/repos/bbylw/Cloudflare-Kitesurf-CN/readme' \
  -H 'Accept: application/vnd.github.raw'
```

3. **获取官方信息**：
   * 官方博客: [https://blog.cloudflare.com/kitesurf/](https://blog.cloudflare.com/kitesurf/)
   * 开发者文档: [https://developers.cloudflare.com/browser-run/kitesurf/](https://developers.cloudflare.com/browser-run/kitesurf/)
   * GitHub 镜像: [https://github.com/bbylw/Cloudflare-Kitesurf-CN](https://github.com/bbylw/Cloudflare-Kitesurf-CN)

## Pitfalls

* **坑**：GitHub API 被代理阻断 → **Fix**：用 `--noproxy '*'` 直连
* **坑**：Jina Reader 不可用 → **Fix**：用 `curl -L` 直接获取 README raw
* **坑**：搜索服务返回空结果 → **Fix**：改用 GitHub API 搜索

## Verification

- [ ] 获取到官方文档链接

- [ ] 记录核心性能指标（CPU 3.1-3.8x, 内存 4.7-7.0x）

- [ ] 确认 CDP 兼容性

- [ ] 列出适用/不适用场景

## Summary

**Kitesurf** = Cloudflare 的 AI Agent 专用无状态浏览器

| **特性** | **详情**                               |
| ------ | ------------------------------------ |
| 架构     | Rust 引擎 + Workers 平台                 |
| 性能     | 内存降低 4.7-7x，CPU 降低 3.1-3.8x          |
| 协议     | 完整 CDP 兼容（Puppeteer/Playwright 直接可用） |
| 合规     | WPT 235k+ 子测试通过                      |
| 成本     | Beta 阶段免费                            |

**适用**：AI Agent 网页渲染、批量抓取、爆发式负载

**不适用**：视频/WebGL、TLS 指纹、像素级测试

**快速上手**：

```bash
# 截图
curl -X POST 'https://api.cloudflare.com/browser-run/screenshot?browser=kitesurf' \
  -H 'Authorization: Bearer <TOKEN>' \
  -d '{"url": "https://example.com"}'
```


