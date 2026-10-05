---
name: vless-uri-config
description: 从 VLESS URI 快速生成 Xray 配置、验证代理是否真正生效、诊断同网段节点问题、配置选择性路由（仅 GitHub/国外走代理）
version: 1.0.0
category: imported
tags: []
metadata:
  hermes:
    tags: []
    source: IMA 知识库导入
---

# vless-uri-config

> 从 VLESS URI 快速生成 Xray 配置、验证代理是否真正生效、诊断同网段节点问题、配置选择性路由（仅 GitHub/国外走代理）。

# VLESS URI 配置与验证

## VLESS URI 字段映射

URI 格式：`vless://UUID@DOMAIN:PORT?security=reality&encryption=none&pbk=KEY&fp=BROWSER&sni=SNI&sid=SHORT_ID`

## 选择性代理路由（2026-08-01）

仅 GitHub/国外网页走代理，国内直连：

```json
"routing": {
  "rules": [
    {"type": "field", "domain": ["geosite:github","geosite:google","domain:github.com","domain:githubusercontent.com"], "outboundTag": "proxy"},
    {"type": "field", "domain": ["geosite:cn"], "outboundTag": "direct"}
  ]
}
```

完整配置见 `references/selective-proxy-routing-2026-08-01.md`

## VLESS URI 字段映射

| **URI 字段** | **Xray 配置位置**                             |
| ---------- | ----------------------------------------- |
| UUID       | `outbounds[].settings.vnext[].users[].id` |
| DOMAIN     | `vnext[].address`                         |
| PORT       | `vnext[].port`                            |
| sni        | `realitySettings.serverName`              |
| pbk        | `realitySettings.publicKey`               |
| sid        | `realitySettings.shortId`                 |
| fp         | `realitySettings.fingerprint`             |

## 配置模板

```json
{
  "inbounds": [
    { "tag": "socks", "port": 10808, "protocol": "socks", "settings": { "udp": true } },
    { "tag": "http",  "port": 10810, "protocol": "http" }
  ],
  "outbounds": [{
    "tag": "proxy",
    "protocol": "vless",
    "settings": {
      "vnext": [{
        "address": "NODE_DOMAIN",
        "port": NODE_PORT,
        "users": [{ "id": "UUID", "encryption": "none" }]
      }]
    },
    "streamSettings": {
      "network": "tcp",
      "security": "reality",
      "realitySettings": {
        "serverName": "SNI_DOMAIN",
        "fingerprint": "BROWSER",
        "shortId": "SHORT_ID",
        "publicKey": "PUBLIC_KEY"
      }
    }
  }]
}
```

## 启动与验证

```bash
xray run -c /tmp/vless-proxy.json &
ss -tlnp | grep -E '10808|10810'
curl -s --proxy socks5://127.0.0.1:10808 https://httpbin.org/ip  # 代理出口
curl -s https://httpbin.org/ip                                     # 直连出口
```

## 诊断：代理未改变出口 IP

**现象**：代理和直连返回相同 IP。

**根因**：代理节点 IP 与服务器在同一网段，或节点未真正穿透 GFW。

**排查**：

1. `dig +short NODE_DOMAIN` — 确认节点 IP
2. 对比直连出口 IP
3. 同网段 → 节点无效，换海外节点

## 2026-08-01 实战：选择性代理路由

### 场景：仅 GitHub/国外网页走代理，其余直连

**问题**：用户需要仅 GitHub 访问走代理，国内访问保持直连。

**解决方案**：Xray routing 规则配置

```json
{
  "routing": {
    "rules": [{
      "type": "field",
      "domain": [
        "geosite:github",
        "geosite:google",
        "geosite:telegram",
        "domain:github.com",
        "domain:githubusercontent.com",
        "domain:githubassets.com",
        "domain:raw.githubusercontent.com"
      ],
      "outboundTag": "proxy"
    },{
      "type": "field",
      "domain": ["geosite:cn"],
      "outboundTag": "direct"
    }]
  }
}
```

**验证方法**：

```bash
# 测试 GitHub（应走代理）
curl -s -x socks5://127.0.0.1:10808 https://api.github.com/zen

# 测试国内（应直连）
curl -s -x socks5://127.0.0.1:10808 https://www.baidu.com
```

**关键结论**：

* 节点 `h.1215719.xyz` 出口 IP `124.243.176.150` 与服务器同网段，**未穿透 GFW**
* 对 Agnes 国外 API 无效，但 **GitHub 访问正常**
* Agnes 国内节点 `apihub.agnes-ai.cn` 直连正常
* **未穿透 GFW**：该节点出口与服务器同网段，对国外 API 无效，但 GitHub 访问正常，无需代理

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

## 触发条件

从 VLESS URI 快速生成 Xray 配置、验证代理是否真正生效、诊断同网段节点问题、配置选择性路由（仅 GitHub/国外走代理）。
