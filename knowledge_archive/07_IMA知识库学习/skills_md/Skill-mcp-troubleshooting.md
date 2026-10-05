# Skill-mcp-troubleshooting

***

name: mcp-troubleshooting
description: MCP 服务器故障诊断与修复。当需要检查 MCP 运行状态、排查连接问题、理解 auto\_disable 机制时使用。触发词：MCP 故障 / 诊断 MCP / 检查 MCP 状态 / MCP 无响应
------------------------------------------------------------------------------------------------------------------

# MCP 故障诊断技能

## 触发条件

* "MCP 故障"、"MCP 无响应"、"检查 MCP 状态"
* "为什么某个 MCP 没有启动"
* "MCP 进程不存在"

## 诊断流程

### Step 1: 检查进程状态

```bash
# 查看所有 MCP 相关进程
ps aux | grep -E 'mcp|context7|sqlite.*mcp|codebase-memory' | grep -v grep

# 统计 watchdog 数量（每个 MCP server 一个 watchdog）
ps aux | grep -c mcp_stdio_watchdog.py
```

### Step 2: 检查配置

```bash
# 查看 config.yaml 中的 MCP 配置
cat ~/.hermes/config.yaml | grep -A 5 'mcp_servers:'

# 检查 enabled 状态
python3 -c "
import yaml
with open('/root/.hermes/config.yaml') as f:
    cfg = yaml.safe_load(f)
servers = cfg.get('mcp', {}).get('mcp_servers', {})
for name, props in servers.items():
    print(f'{name}: enabled={props.get(\"enabled\", True)}')
"
```

### Step 3: 检查二进制文件

```bash
# 检查常用 MCP binary
ls -la /root/.local/bin/codebase-memory-mcp
which mcp-server-sqlite
which npx
```

### Step 4: 判断状态

| **情况**              | **判断** | **处理**                 |
| ------------------- | ------ | ---------------------- |
| 进程存在 + enabled=true | ✅ 正常   | 无需操作                   |
| Binary 存在但无进程       | ⚠️ 未启动 | 检查 watchdog，重启 Hermes  |
| Binary 不存在          | ❌ 未安装  | 执行安装                   |
| enabled=false       | 🚫 已禁用 | 符合预期（auto\_disable 正常） |

## Pitfalls

| **坑**                             | **症状**                     | **Fix**                                                          |                                               |
| --------------------------------- | -------------------------- | ---------------------------------------------------------------- | --------------------------------------------- |
| **Binary 存在但无进程**                 | enabled: true 但进程不存在       | 检查 watchdog：\`ps aux                                             | grep mcp\_stdio\_watchdog.py\`。可能是 Hermes 未重启 |
| **auto\_disable 正常现象**            | anysearch/activepieces 被禁用 | 这是 mcp\_tiers 的保护机制，非故障。检查 `mcp_tiers.auto_disable_low_priority` |                                               |
| **Agent 模式无法执行 `hermes mcp add`** | 命令超时                       | 手动编辑 config.yaml                                                 |                                               |

## 参考

* [references/mcp-health-check.md](references/mcp-health-check.md) - 健康检查命令汇总
* [mcp](mcp) - MCP 配置基础技能

## 验证

- [ ] 确认所有 enabled: true 的 server 都有对应进程

- [ ] 确认 auto_disable 列表中的 server 被正确禁用

- [ ] 输出当前状态摘要
