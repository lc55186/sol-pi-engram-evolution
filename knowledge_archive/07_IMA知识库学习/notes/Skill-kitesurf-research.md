Skill-kitesurf-researchname: kitesurf-research
description: |
研究 Kitesurf（Cloudflare AI Agent 专用浏览器）。当用户询问/研究/评估 Kitesurf 或 AI Agent 专用浏览器时激活。触发词：Kitesurf / AI 专用浏览器 / Cloudflare 浏览器 / 无状态浏览器。
version: 1.0.0
author: Hermes
license: MIT
platforms: [linux, macos, win]
metadata:
hermes:
tags: [kitesurf, browser, research, cloudflare]
category: research
requires_toolsets: [terminal, web]Kitesurf Research — Cloudflare AI Agent 浏览器When to Use用户询问 Kitesurf 浏览器能力评估 AI Agent 专用浏览器方案对比 Kitesurf vs Puppeteer/Playwright vs Chromium研究无状态浏览器架构Procedure搜索 GitHub（备用方案，因搜索服务常不可用）：curl -sL --noproxy '*' --connect-timeout 10 --max-time 20 \  'https://api.github.com/search/repositories?q=kitesurf+AI+agent+browser&sort=stars&order=desc&per_page=10'读取 README（官方文档）：curl -sL --noproxy '*' --connect-timeout 10 --max-time 20 \  'https://api.github.com/repos/bbylw/Cloudflare-Kitesurf-CN/readme' \  -H 'Accept: application/vnd.github.raw'获取官方信息：官方博客: https://blog.cloudflare.com/kitesurf/开发者文档: https://developers.cloudflare.com/browser-run/kitesurf/GitHub 镜像: https://github.com/bbylw/Cloudflare-Kitesurf-CNPitfalls坑：GitHub API 被代理阻断 → Fix：用 --noproxy '*' 直连坑：Jina Reader 不可用 → Fix：用 curl -L 直接获取 README raw坑：搜索服务返回空结果 → Fix：改用 GitHub API 搜索Verification获取到官方文档链接记录核心性能指标（CPU 3.1-3.8x, 内存 4.7-7.0x）确认 CDP 兼容性列出适用/不适用场景SummaryKitesurf = Cloudflare 的 AI Agent 专用无状态浏览器特性详情架构Rust 引擎 + Workers 平台性能内存降低 4.7-7x，CPU 降低 3.1-3.8x协议完整 CDP 兼容（Puppeteer/Playwright 直接可用）合规WPT 235k+ 子测试通过成本Beta 阶段免费适用：AI Agent 网页渲染、批量抓取、爆发式负载不适用：视频/WebGL、TLS 指纹、像素级测试快速上手：# 截图curl -X POST 'https://api.cloudflare.com/browser-run/screenshot?browser=kitesurf' \  -H 'Authorization: Bearer <TOKEN>' \  -d '{"url": "https://example.com"}'