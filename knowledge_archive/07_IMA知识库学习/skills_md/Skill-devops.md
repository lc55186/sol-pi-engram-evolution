# Skill-devops

***

name: devops
description: "运维开发技能包：模型配置、多分身管理、Agent持续性、视频编码、系统优化、网络代理。 触发词：模型配置 / fallback / 模型切换 / 分身管理 / profile / Agent持续性 / 反思循环 / 视频编码 / 视频转码 / system prompt优化 / token优化 / 代理 / 翻墙 / 外网 / 出站代理 / Xray / VLESS / Trojan / 机场。 适用：管理Hermes配置、创建Agent分身、处理视频、优化系统性能、配置网络代理。 反例：不要触发于纯代码开发、文本写作、非Hermes系统的运维。"
version: 2.2.0
author: Hermes
license: MIT
platforms: \[linux, macos]
metadata:
hermes:
tags: \[devops, ops, model-config, profiles, consciousness, video-encoding, optimization]
category: ops
requires\_toolsets: \[terminal, file]
-------------------------------------

# DevOps — 运维开发技能包

> 本 Skill 是运维开发任务的**路由入口**。先匹配子技能，再加载对应的 SKILL.md 执行。

## Communication Style

* **语言**：中文为主，命令和技术术语保留英文
* **结构**：先匹配路由 → 加载子技能 → 按步骤执行 → 输出 verdict
* **语气**：命令式，给出可直接执行的命令，不解释 shell 基础
* **受众**：有终端权限的运维开发者
* **禁忌**：不在改配置前不备份，不在跨 profile 操作前不确认

## Success Criteria

- [ ] 正确匹配路由表中的子技能

- [ ] 执行后输出 Ops Verdict（SUCCESS/PARTIAL/FAILED）

- [ ] 有明确的回滚方式

- [ ] 配置变更前先备份

- [ ] 跨 profile 操作前确认当前 profile 路径

## When to Use

* 用户说"模型配置"、"fallback"、"模型切换"、"辅助模型"
* 用户说"分身管理"、"创建profile"、"多Agent"
* 用户说"Agent持续性"、"反思循环"、"守护进程"
* 用户说"视频编码"、"视频转码"、"ffmpeg"
* 用户说"系统优化"、"token优化"、"prompt优化"
* 用户说"代理"、"翻墙"、"出站代理"、"Xray"、"VLESS"、"Trojan"、"Reality"
* 用户说"磁盘清理"、"日志归档"、"根目录归档"、"系统清理"
* 用户说"Activepieces"、"工作流自动化"、"MCP集成"
* 用户说"迁移"、"搬家"、"平移"、"转移到笔记本"、"环境迁移"

## Prerequisites

- [ ] Hermes 已安装且可执行（hermes --version）

- [ ] 有终端权限（所有运维操作都需要）

- [ ] 有文件系统读写权限

## Procedure: 路由表

根据用户需求，匹配以下子技能，然后 **用 skill\_view 加载对应 SKILL.md 并按其中的 Procedure 执行**：

### 路由规则

| **用户需求关键词**                                  | **子技能**                                   | **SKILL.md 路径**                                      | **执行方式**           |
| -------------------------------------------- | ----------------------------------------- | ---------------------------------------------------- | ------------------ |
| 模型配置、fallback、模型切换、辅助模型、模型测试                 | `hermes-model-configuration`              | `hermes-model-configuration/SKILL.md`                | 加载后按其中步骤执行         |
| 分身、profile、多Agent、分身管理                       | `hermes-profiles`                         | `hermes-profiles/SKILL.md`                           | 加载后按其中步骤执行         |
| Agent持续性、反思循环、自我模型、守护进程、consciousness        | `agent-consciousness`                     | `agent-consciousness/SKILL.md`                       | 加载后按其中步骤执行         |
| 视频编码、视频转码、ffmpeg、视频交付                        | `linux-media-video-encoding`              | `linux-media-video-encoding/SKILL.md`                | 加载后按其中步骤执行         |
| system prompt、token优化、prompt优化、上下文压缩         | `system-prompt-optimization`              | `system-prompt-optimization/SKILL.md`                | 加载后按其中步骤执行         |
| Skill编写规范、创建Skill                            | `skill-authoring`                         | `skill-authoring/SKILL.md`                           | 加载后按其中步骤执行         |
| 记忆写入、shadow write                            | `shadow-write-pipeline`                   | `shadow-write-pipeline/SKILL.md`                     | 加载后按其中步骤执行         |
| 代理、翻墙、出站代理、Xray、VLESS、Trojan、Reality、机场、外网访问 | `outbound-proxy-setup`                    | `outbound-proxy-setup/SKILL.md`                      | 加载后按其中步骤执行         |
| 磁盘清理、日志归档、根目录归档、系统维护                         | 本 Skill 的 `System Housekeeping` 流程        | 本 Skill 的 `references/system-housekeeping.md`        | 加载后按其中的流程执行归档/清理操作 |
| 休眠项目检测/归档/优化/集成                              | 本 Skill 的 `Sleeping Project Lifecycle` 流程 | 本 Skill 的 `references/sleeping-project-lifecycle.md` | 加载后按其中的流程执行        |
| Activepieces 部署、工作流自动化、MCP 集成                | 本 Skill 的 Activepieces 流程                 | 本 Skill 的 `references/activepieces-deployment.md`    | 加载后按其中的步骤部署        |
| 环境迁移、服务器平移、Hermes搬家、迁移到笔记本                   | 本 Skill 的 `Environment Migration` 流程      | 本 Skill 的 `references/environment-migration.md`      | 加载后按其中的流程执行        |

### 执行步骤

1. **识别用户需求** → 匹配路由表中的子技能
2. **加载子技能**: `skill_view(name='<子技能名>')` 或 `skill_view(name='devops', file_path='references/system-housekeeping.md')`
3. **执行子技能**: 按子技能中的 Procedure 步骤链执行
4. **验证结果**: 按子技能的 Verification 输出 verdict

## System Housekeeping（磁盘/归档/清理）

当触发词为"磁盘清理"、"日志归档"、"根目录归档"、"系统清理"时：

1. 加载 `skill_view(name='devops', file_path='references/system-housekeeping.md')`
2. 按其中的流程执行归档/清理操作
3. 所有操作记录到 `~/.hermes/logs/daily/YYYY-MM-DD.md`

## Delivery Checklist

交付前逐项确认：

- [ ] 正确识别了用户需求并匹配到路由表中的子技能

- [ ] 加载了对应的子技能 SKILL.md

- [ ] 按子技能的 Procedure 步骤链执行完毕

- [ ] 配置变更前已备份（cp xxx xxx.bak）

- [ ] 跨 profile 操作前确认了当前 profile 路径

- [ ] Ops Verdict 输出完整：操作/状态/影响/回滚方式/下一步

- [ ] 回滚方式可行（不是"无"）

## Pitfalls

| **坑**                    | **症状**                                                                                                         | **Fix**                                                                                                                                                                                                                                                                                                                       |
| ------------------------ | -------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **直接猜测配置结构**             | 配错模型导致 API 调不通                                                                                                 | 必须先加载 `hermes-model-configuration` SKILL.md，不要手动猜                                                                                                                                                                                                                                                                             |
| **混淆 profile 和 skill**   | 在错误的目录创建文件                                                                                                     | profile 管理隔离状态，skill 管理可执行知识，不要混淆                                                                                                                                                                                                                                                                                             |
| **视频编码忽略容器限制**           | ffmpeg 命令跑不了                                                                                                   | 先检查 ffmpeg 版本和可用编码器，加载 `linux-media-video-encoding`                                                                                                                                                                                                                                                                           |
| **修改配置不备份**              | 配置改坏无法回滚                                                                                                       | 修改前先 `cp config.yaml config.yaml.bak`                                                                                                                                                                                                                                                                                         |
| **跨 profile 操作**         | 误改其他 profile 的文件                                                                                               | 确认当前 profile 路径再操作，不要假设                                                                                                                                                                                                                                                                                                       |
| **Docker Compose 服务未缩进** | 运行 `docker compose up` 报错 "services must be a mapping"                                                         | 确保每个服务（如 `searxng`）在 `docker-compose.yml` 中缩进2格下，符合YAML格式要求                                                                                                                                                                                                                                                                   |
| **系统文件修改权限不足**           | 用 `patch` / `write_file` 改 `/etc/xxx/xxx.conf` 报错权限拒绝                                                          | 改用 `terminal` 命令执行 `echo 'content' > /etc/xxx/xxx.conf`，获取root权限后写入                                                                                                                                                                                                                                                           |
| **PHP-FPM 文件所有权**        | `write_file`/`patch` 修改 `/var/www/html/api/*.php` 后文件变为 `root:root`，PHP-FPM 以 `apache` 用户运行报 Permission denied | 每次文件修改后执行 `chown apache:apache /var/www/html/api/*.php`，这是 Hermes 工具链的已知行为                                                                                                                                                                                                                                                    |
| **本地 SearXNG 镜像拉取失败**    | Docker pull 因网络/registry问题失败                                                                                   | 1. 先验证基础Docker功能：执行 `sudo docker pull nginx:alpine`，确认Docker配置正常；若基础镜像拉取失败，需先解决Docker网络/镜像源问题；2. 临时切换到公共 SearXNG 实例（如 `https://searx.be`），修改 `~/.hermes/config.yaml` 中 `web.searxng_url` 配置；3. 若需使用本地镜像，先配置Docker代理：创建/修改 `/etc/systemd/system/docker.service.d/http-proxy.conf`，添加 `HTTP_PROXY`/`HTTPS_PROXY` 环境变量，然后重启docke |
