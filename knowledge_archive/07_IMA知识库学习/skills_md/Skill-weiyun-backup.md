# Skill-weiyun-backup

***

name: weiyun-backup
version: "1.2.0"
description: >-
微云网盘自动备份工作流。将 Hermes 核心数据或项目文件打包上传到微云，并生成备份报告同步到 IMA 知识库。
支持两种场景：(1) Hermes 核心数据定期备份 (2) 项目级打包备份（源代码/文档/配置/知识库分包上传，用于项目平移）。
触发词：微云备份 / weiyun backup / 备份到微云 / 云端备份 / 增量备份 / 项目备份 / 项目平移。
当需要将本地数据或项目备份到微云网盘时使用。
metadata:
hermes:
tags: \[backup, weiyun, cloud, automation, cron]
related\_skills: \[ima, sysops-toolkit, deployment-troubleshooting]
requires\_toolsets: \[terminal, file]
-------------------------------------

# 微云备份工作流

> 一句话定位：将 Hermes 核心数据自动打包上传到微云网盘，并生成备份报告同步到 IMA 知识库。

## 体系架构

```
Weiyun Backup Workflow
├── 备份脚本: scripts/weiyun_backup.py (增量打包 + 上传)
├── 报告生成: scripts/generate_backup_report.py (结构化报告)
├── IMA 上传: scripts/upload_backup_to_ima.py (报告同步到知识库)
├── Cron 任务: weiyun-daily-backup (每天 03:00 自动执行)
└── 微云目录: .hermes_backup/{core_data, reports, learning_assets, scripts_backup}
```

## 触发条件

| **触发词**                   | **动作**                             |
| ------------------------- | ---------------------------------- |
| "备份到微云" / "weiyun backup" | 执行完整备份流程                           |
| "查看备份报告" / "备份状态"         | 读取 backup\_report.json 并展示         |
| "上传备份报告到 IMA"             | 执行 upload\_backup\_to\_ima.py      |
| "手动触发备份"                  | 运行 weiyun\_backup.py --incremental |

## Procedure

### 1. 初始化微云目录（首次使用）

```bash
# 创建备份根目录
mcporter call --server weiyun --tool weiyun.create_dir \
  pdir_key=a803ed01f0a739ae12b58dcd423dce4a \
  dir_name=.hermes_backup --output json

# 创建子目录
mcporter call --server weiyun --tool weiyun.create_dir \
  pdir_key=<根目录dir_key> dir_name=core_data --output json
mcporter call --server weiyun --tool weiyun.create_dir \
  pdir_key=<根目录dir_key> dir_name=reports --output json
mcporter call --server weiyun --tool weiyun.create_dir \
  pdir_key=<根目录dir_key> dir_name=learning_assets --output json
mcporter call --server weiyun --tool weiyun.create_dir \
  pdir_key=<根目录dir_key> dir_name=scripts_backup --output json
```

### 2. 执行备份

```bash
export WEIYUN_MCP_TOKEN="<token>"
python3 /root/.hermes/scripts/weiyun_backup.py --incremental
```

备份文件列表：

* state.db → core\_data
* memory/, skills/, workspace/, profiles/, cron/ → core\_data
* config.yaml, knowledge\_base/ → reports
* learning/ → learning\_assets
* scripts/ → scripts\_backup

### 3. 生成备份报告

```bash
python3 /root/.hermes/scripts/generate_backup_report.py
```

报告保存在 `~/.hermes/backup/backup_report.json`。

### 4. 上传报告到 IMA（可选）

```bash
python3 /root/.hermes/scripts/upload_backup_to_ima.py
```

## 项目级备份（项目平移场景）

当需要将整个项目打包上传到微云以便平移到其他服务器时：

### 分包策略

| **包类型** | **内容**                                           | **命名规范**                         | **优先级** |
| ------- | ------------------------------------------------ | -------------------------------- | ------- |
| 源代码包    | src/, tests/, 核心模块                               | `{project}-source-only.tar.gz`   | P0      |
| 文档包     | docs/, patents/, 设计文档                            | `{project}-docs.tar.gz`          | P0      |
| 配置包     | docker-compose.yml, Dockerfile, requirements.txt | `{project}-config-deploy.tar.gz` | P1      |
| 知识库包    | learning/, memories/                             | `{project}-knowledge.tar.gz`     | P2      |
| 完整包     | 所有内容                                             | `{project}-full-backup.tar.gz`   | 备选      |

### 分包上传流程

```bash
# 1. 创建微云目录
mcporter call --server weiyun --tool weiyun.create_dir \
  pdir_key=<父目录dir_key> dir_name="{项目名}备份" --output json

# 2. 分包打包（避免单包超过50MB触发限流）
cd /path/to/project
tar -czf /tmp/{project}-source-only.tar.gz src/ tests/ --exclude='node_modules' --exclude='__pycache__'

# 3. 逐包上传
FILE="/tmp/{project}-source-only.tar.gz"
FILE_SHA=$(sha1sum "$FILE" | awk '{print $1}')
FILE_SIZE=$(stat -c%s "$FILE")

mcporter call --server weiyun --tool weiyun.upload --args "{
  \"filename\": \"$(basename $FILE)\",
  \"file_sha\": \"$FILE_SHA\",
  \"file_size\": $FILE_SIZE,
  \"block_sha_list\": [\"$FILE_SHA\"],
  \"pdir_key\": \"<目标目录dir_key>\"
}" --output json
```

### 验证上传完整性

```bash
# 验证微云目录文件数量
mcporter call --server weiyun --tool weiyun.list \
  --args '{"pdir_key": "<目录dir_key>", "limit": 50}' --output json

# 统计文件数量
cat /tmp/list_result.json | grep -c '"file_size"'
```

### 恢复指南模板

```bash
# 1. 下载所有备份文件
# 2. 解压源代码
tar -xzf {project}-source-only.tar.gz
# 3. 解压文档
tar -xzf {project}-docs.tar.gz
# 4. 解压配置
tar -xzf {project}-config-deploy.tar.gz
# 5. 安装依赖
pip install -r requirements.txt
# 6. 启动服务
docker-compose up -d
```

## Pitfalls

| **坑**                                         | **症状**                                                                                       | **Fix**                                                                                                                  |
| --------------------------------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **大文件上传被限流**                                  | 返回 `concurrent request limited` 错误，上传失败                                                      | 分包上传：单包控制在 50MB 以内；或等待 2-3 分钟后重试                                                                                         |
| **\_encoding\_fix 模块缺失**                      | upload\_to\_weiyun.py 报错 `ModuleNotFoundError: No module named '_encoding_fix'`              | 在 `scripts/` 目录下创建 `_encoding_fix.py`（Linux UTF-8 编码修复）                                                                  |
| **mcporter 调用格式错误**                           | 直接写 `mcporter call weiyun.list` 导致 server/tool 拆分错误                                          | 必须用 `mcporter call --server weiyun --tool weiyun.xxx` 格式                                                                 |
| **大文件上传超时**                                   | state.db >200MB 上传超过 300s                                                                    | 增加 timeout 到 600s，或分批次备份                                                                                                 |
| **Token 未设置**                                 | 上传脚本提示 `错误：必须提供 MCP token`                                                                   | 通过 `WEIYUN_MCP_TOKEN` 环境变量或 `--token` 参数传入                                                                               |
| **备份目录不存在**                                   | 上传到不存在的 dir\_key                                                                             | 先创建目录并记录 dir\_key                                                                                                        |
| **state.db 过大导致备份超时**                         | 754MB state.db 打包+上传超过 10 分钟                                                                 | 分两步：先打包小文件，state.db 单独上传；或只备份最近 7 天会话                                                                                    |
| **微云上传目录 pdir\_key 错误**                       | 上传到错误目录或失败                                                                                   | 通过 `mcporter call --server weiyun --tool weiyun.list` 获取正确 pdir\_key                                                     |
| **file\_list 不返回文件名**                         | 无法通过 list 结果判断文件是否存在                                                                         | 用 `weiyun.upload` 的 `file_exist` 字段验证（基于 SHA1 去重）                                                                        |
| **完整包上传失败**                                   | 大项目完整包超过 200MB 上传失败                                                                          | 改用分包策略：源代码/文档/配置/知识库分别打包上传                                                                                               |
| **微云服务器繁忙**                                   | 返回 `retcode=-89016, retmsg=(-89016)服务器繁忙`，channel\_list 为空                                   | 等待 60s 后重试，最多 3 次；若持续失败可能是微云服务端维护，需稍后再试。不要连续快速重试，会加剧限流                                                                   |
| **微云隐性大小限制**                                  | 完整包(934K)持续失败，但分包(76K+64K)成功上传                                                               | 上传文件可能有隐性大小阈值(约100K+)。大项目必须分包：源代码/文档/配置分别打包上传                                                                            |
| **大文件微云不可行**                                  | 71MB分包上传需要数百次调用，实际不可行                                                                        | 超过1MB的文件不要走微云。切换备选传输方案（见下方"备选传输方案"）                                                                                      |
| **list API pdir\_key 被忽略**                    | `weiyun.list` 传入 `pdir_key` 但始终返回根目录内容                                                       | 这是 mcporter/weiyun API 的已知 bug；验证目录内容时用 `weiyun.upload` 的 `file_exist` 字段（SHA1 去重）来判断文件是否已存在                             |
| **profiles/ 打包超时**                            | `profiles/` 目录超过 1GB 时 `tar -czf` 超过 120s 导致备份脚本中断                                           | 排除 profiles/ 目录，只备份核心数据（state.db、config.yaml、skills/、memory/、cron/、scripts/）。profiles/ 可通过 `hermes profiles export` 单独处理 |
| **cron 环境无环境变量**                              | 定时任务中 `export WEIYUN_MCP_TOKEN` 不生效，Python 脚本报"必须提供 MCP token"                               | Cron wrapper 脚本必须在调用 Python 前显式 `export`，或使用 `--token` 参数传入；不要依赖 shell 的 `.bashrc` / `.profile`（cron 不加载这些文件）            |
| **upload 缺少 file\_data 返回 filename required** | 调用 `weiyun.upload` 只传 filename/pdir\_key/file\_sha 等元数据，返回 `"error": "filename is required"` | 微云上传分两步：Step 1 预上传获取 upload\_key + channel\_list；Step 2 携带 `file_data`（base64 编码文件内容）实际上传。仅传元数据不会触发上传                    |
| **微云连接超时**                                    | `Connect Timeout Error (attempted addresses: 111.31.2.x:443)`                                | 微云服务端不可用，需等待恢复；备份文件保留在本地 `/tmp/` 或项目目录，服务恢复后手动上传                                                                         |

## Verification

1. 检查 backup\_log.json 中最新记录的 uploaded\_count > 0
2. 检查微云目录是否有新上传的文件
3. 验证 backup\_report.json 格式正确
4. （可选）检查 IMA 知识库是否有新笔记

## 备选传输方案（微云不可用时）

当文件超过微云隐性限制（\~100KB+）或微云服务不可用时，按优先级选择：

| **方案**        | **适用场景**          | **命令/方法**                       | **注意事项**                                                 |
| ------------- | ----------------- | ------------------------------- | -------------------------------------------------------- |
| **SCP/SFTP**  | 目标机器有SSH访问权限      | `scp root@<IP>:<path> .`        | 最可靠，需知道密码或有密钥                                            |
| **飞书文件发送**    | 用户在飞书对话中          | 在回复中包含 `MEDIA:/path/to/file`    | 飞书原生支持，无需额外配置                                            |
| **临时HTTP服务器** | 目标可访问服务器端口        | `python3 -m http.server <port>` | ⚠️ 云安全组可能拦截端口，先用 `curl localhost:<port>` 验证本地可达，再检查外网可达性 |
| **微云分包**      | 文件 \<100KB 且无其他方案 | 标准分包上传流程                        | 仅适合小文件                                                   |

**云安全组陷阱**：临时HTTP服务器在云服务器上几乎必定被安全组拦截。验证步骤：

1. `ss -tlnp | grep <port>` — 确认监听
2. `curl localhost:<port>` — 确认本地可达
3. `curl <公网IP>:<port>` — 确认外网可达（这步经常失败）
4. 若外网不通，直接放弃HTTP方案，改用SCP或飞书发送

## 单文件上传（非备份场景）

当需要上传单个或多个文件到微云（而非执行完整备份）时：

### 快速上传流程

```bash
export WEIYUN_MCP_TOKEN="<token>"

# 1. 检查文件是否已存在（基于 SHA1 去重）
FILE="/path/to/file.md"
FILE_SHA=$(sha1sum "$FILE" | awk '{print $1}')
FILE_SIZE=$(stat -c%s "$FILE")

# 2. 执行上传
mcporter call --server weiyun --tool weiyun.upload --args "{
  \"filename\": \"$(basename $FILE)\",
  \"file_sha\": \"$FILE_SHA\",
  \"file_size\": $FILE_SIZE,
  \"block_sha_list\": [\"$FILE_SHA\"],
  \"pdir_key\": \"<目标目录dir_key>\"
}" --output json
```

### 去重机制

* 相同 SHA1 的文件会**秒传**（不实际传输数据）
* 返回 `file_exist: true` 表示文件已存在
* 适用于相同内容在不同目录下的重复上传

### 常见问题

| **问题**            | **原因**    | **解决方案**                              |
| ----------------- | --------- | ------------------------------------- |
| file\_list 中没有文件名 | 微云 API 设计 | 用 `weiyun.upload` 的 `file_exist` 字段验证 |
| 上传超时              | 大文件或网络问题  | 增加 timeout 或分块上传                      |
| channel\_list 为空  | 预上传失败     | 重试或检查 token                           |

详细机制见 `references/upload-mechanism.md`。

## Related Files

* `scripts/weiyun_backup.py` — 主备份脚本
* `scripts/generate_backup_report.py` — 报告生成
* `scripts/upload_backup_to_ima.py` — IMA 上传
* `references/mcporter-format.md` — mcporter 调用格式说明
* `references/upload-mechanism.md` — 上传机制详解（去重、流程、调试）
* `references/project-sync-pattern.md` — 项目持续同步模式（增量检测、状态追踪、退避重试）
* `references/cron-env-pitfall.md` — Cron 环境变量陷阱及修复方案
* `references/backup-fallback-pattern.md` — tar 安全策略绕过方案（Python tarfile 替代）

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
