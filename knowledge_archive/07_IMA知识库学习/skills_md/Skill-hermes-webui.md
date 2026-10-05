# Skill-hermes-webui

***

name: hermes-webui
description: >-
Hermes 内置 WebUI（v0.16.0+，v0.17.0 认证安全加固，升级日志见 references/v0.17.0-upgrade-log.md）：通过 `python -m hermes_cli.main dashboard` 启动，
基于 FastAPI + uvicorn 的内置后端 + Vite/React 前端。覆盖：启动配置、Host header
陷阱、v0.17.0 认证绑定变更（0.0.0.0 需 auth）、端口冲突处理、WebUI dist 重建、
故障排查、升级日志。
触发词：webui / dashboard / Web UI / 打开面板 / 启动界面 / 升级webui
version: 2.0.0
author: EKKO Team
license: MIT
metadata:
hermes:
tags: \[webui, interface, dashboard, tui, web, vue, typescript]
homepage: [https://github.com/nesquena/hermes-webui](https://github.com/nesquena/hermes-webui)related\_skills: \[hermes-agent]
------------------------------------------------------------------------------------------------------------------------------

# Hermes WebUI - Lightweight Web Interface

> **内置功能**: Hermes v0.16.0+ 内置 WebUI 后端（`hermes_cli.web_server`，基于 FastAPI + uvicorn）+ 前端构建产物（`hermes_cli/web_dist/`，Vite/React/TypeScript）。无需 Node.js、无需外部仓库。

Hermes WebUI provides a beautiful, lightweight web interface for Hermes Agent that delivers nearly 1:1 parity with the CLI experience. Access your Hermes Agent securely through any modern web browser with full terminal functionality, file management, and real-time collaboration features.

## Architecture

```
python -m hermes_cli.main dashboard --host 0.0.0.0 --port 8787
  ↓
Lazy-import: fastapi + uvicorn (自动安装)
  ↓
web_dist/ (Vite/React SPA, 预构建)
  ↓
浏览器访问: GET / → 200 + index.html + JS/CSS
```

## 前置依赖

* Python 3.12+ ✅
* fastapi 0.136.1 + uvicorn (WebUI 启动时自动 lazy-install) ✅
* Node.js / npm: **不需要** ✅
* 外部 git clone: **不需要** ✅

## 🌟 Why Hermes WebUI?

### 🚀 Key Advantages

* **CLI Parity**: Every CLI command available in the web interface
* **Secure Access**: SSH tunnel security without exposing ports publicly
* **Multi-Platform**: Works on desktop, tablet, and mobile devices
* **Real-Time**: Live updates without page refreshes
* **Offline Support**: Works even with intermittent connectivity

## 📱 Interface Overview

### Main Layout

```
┌─────────────────────────────────────────────────────────────┐
│ 🏠 Home 📊 Sessions ⚙️ Settings 👤 Profile 📈 Analytics     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐ ┌───────────────────────────────────┐ │
│  │   Chat Panel    │ │        Terminal Panel             │ │
│  │                 │ │                                   │ │
│  │ 💬 Hermes Chat  │ │ 🖥️ Command Line Interface         │ │
│  │                 │ │                                   │ │
│  └─────────────────┘ └───────────────────────────────────┘ │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    File Browser                         │ │
│  │ 📁 Documents 📁 Projects 📁 Configs 📁 Skills           │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

> **内置 WebUI**: Hermes v0.16.0+ 内置 WebUI（`hermes_cli.web_server`），无需 `git clone` 外部项目。直接使用 `python -m hermes_cli.main dashboard` 启动。

### 启动内置 WebUI

```bash
cd /root/hermes-agent

# 本地访问（默认 127.0.0.1:9119）
python -m hermes_cli.main dashboard

# 远程访问（绑定所有接口，推荐）
python -m hermes_cli.main dashboard --host 0.0.0.0 --port 8787 --no-open --skip-build --insecure
```

### 前置依赖

* Python 3.12+ ✅
* fastapi + uvicorn（WebUI 启动时自动 lazy-install）✅

> **旧版外部 WebUI** (nesquena/hermes-webui) 已废弃，不要再用 `git clone` + `npm install` 方式。内置版本直接使用 Python 模块，无需 Node.js/npm。

## 🛠️ Core Features

### 💬 Chat Interface

* **Real-time messaging**: Instant responses from Hermes Agent
* **File attachments**: Upload images, documents, and code snippets
* **Voice support**: Text-to-speech and speech-to-text integration
* **Session management**: Multiple concurrent conversations

### 🖥️ Terminal Emulator

* **Full CLI access**: All Hermes commands available
* **Command history**: Searchable command log with autocomplete
* **Multiple tabs**: Separate terminals for different tasks
* **Output formatting**: Syntax highlighting and collapsible sections

### 📁 File Management

* **Drag & drop**: Easy file upload and organization
* **Preview modes**: Built-in preview for common file types
* **Remote editing**: Direct file modification through the browser

## 🛠️ Core Features

### ⚙️ Configuration Panel

* **Model selection**: Switch between different AI models (auto-syncs with Hermes Agent's primary model by default)
* **Tool management**: Enable/disable specific capabilities
* **Theme customization**: Dark/light mode and color schemes
* **Keyboard shortcuts**: Customizable hotkeys for power users

### 💬 Chat / Dialogue (--tui flag)

> **关键发现**: WebUI 的对话功能（Chat tab）**仅在 `--tui` 参数下启用**。不加 `--tui` 启动时，只能看到看板/仪表盘界面，无法对话。

```bash
# ✅ 有对话功能
python -m hermes_cli.main dashboard --host 0.0.0.0 --port 8787 --no-open --skip-build --insecure --tui

# ❌ 无对话功能（仅看板）
python -m hermes_cli.main dashboard --host 0.0.0.0 --port 8787 --no-open --skip-build --insecure
```

**原理**: \`
