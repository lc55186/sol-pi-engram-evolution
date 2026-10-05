# Skill-hc-project-maintenance

***

name: hc-project-maintenance
version: 1.0.0
description: "HC 社区项目维护：多服务器同步故障诊断、残留文件清点、源码恢复、状态报告生成。当 HC-BAK 服务器不可达、项目同步失败、或需要恢复 HC 项目时加载。"
category: devops
tags: \[HC项目, 多服务器同步, 故障诊断, 源码恢复, 运维]
-------------------------------------

# HC 社区项目维护

## 概述

HC 社区是智慧社区 SaaS 系统，包含 8 个子项目模块（P01-P08），部署在 HC-BAK (172.16.16.100) 服务器上。本机 (LYH-01 172.16.10.108) 定期同步项目档案。

***

## 故障诊断流程

### 1. 网络连通性检测

```bash
# ARP 邻居表
ip neigh show | grep 172.16.16.100
# 状态: REACHABLE/FAILED/STALE

# 路由表
route -n | grep 172.16

# 本机 IP
hostname -I

# SSH 连接测试
ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no 172.16.16.100 'hostname'
```

### 2. 本机残留文件清点

```bash
ls -la /opt/hc-project/
```

| **目录**              | **状态**                 |
| ------------------- | ---------------------- |
| ops-panel/          | ⚠️ server.js 残留（进程未运行） |
| pc-owner/           | ⚠️ index.html 残留       |
| pc-property/        | ⚠️ index.html 残留       |
| MicroCommunity/     | 🔴 已丢失                 |
| MicroCommunityIot/  | 🔴 已丢失                 |
| MicroCommunityWeb/  | 🔴 已丢失                 |
| WechatOwnerService/ | 🔴 已丢失                 |
| PropertyApp/        | 🔴 已丢失                 |

### 3. 服务端口状态

```bash
ss -tlnp | grep -E '(8008|9001|9002|9091|9999|20011)'
ps aux | grep -E '(MicroCommunity|iot-boot|ops-panel)' | grep -v grep
```

***

## 远程仓库信息

| **项目**                 | **Git 远程**                           | **最后提交**             |
| ---------------------- | ------------------------------------ | -------------------- |
| P01 MicroCommunity     | origin/master                        | da7fe27 (2026-06-27) |
| P02 MicroCommunityIot  | origin/master                        | 3e43e9a (2026-06-17) |
| P03 MicroCommunityWeb  | gitee.com/java110/MicroCommunityWeb  | 2beee9d60            |
| P04 WechatOwnerService | gitee.com/java110/WechatOwnerService | 7f6a8dc              |
| P05 PropertyApp        | -                                    | 7454b77              |

***

## 源码恢复命令

```bash
# 从 Gitee 恢复（需配置 SSH 密钥或 token）
cd /opt/hc-project
git clone https://gitee.com/java110/MicroCommunityWeb.git
git clone https://gitee.com/java110/WechatOwnerService.git
# P01/P02 需从 origin/master 恢复
```

***

## 行动项模板

| **优先级** | **任务**                       | **负责人** | **状态** |
| ------- | ---------------------------- | ------- | ------ |
| 🔴 高    | 物理确认 HC-BAK 服务器状态            | 运维      | 待处理    |
| 🔴 高    | 恢复 P01-P05 源码（从 Gitee clone） | Agent   | 待处理    |
| 🟡 中    | HC-BAK 重建部署                  | 运维      | 待处理    |
| 🟡 中    | 建立自动备份机制                     | Agent   | 待处理    |

***

## 端口拓扑

```
Internet → 防火墙 → Nginx (0.0.0.0:80/9001/9002/9093/9094)
                              │
                              ├─ :80   → MicroCommunityWeb/dist (前端静态)
                              ├─ :9001 → pc-owner (业主版前端)
                              ├─ :9002 → pc-property (物业版前端)
                              ├─ :9091 → ops-panel (Node.js 运维面板)
                              └─ :9090 → Cockpit/Web VNC 控制台

直连端口（localhost only）:
  127.0.0.1:8008  → MicroCommunity (Spring Boot) ⚠️ DOWN
  127.0.0.1:9999  → MicroCommunityIot (Spring Boot) ✅
  127.0.0.1:3306  → MySQL
  127.0.0.1:6379  → Valkey (Redis)
```

***

## 已知 Pitfalls

1. **HC-BAK 不可达时本机残留文件易被误认为完整备份** - 实际 P01-P05 源码目录已丢失
2. **端口 9999 可能被多个服务占用** - hermes-cloud API 也使用此端口，需确认进程
3. **Gitee 克隆需配置认证** - 部分仓库可能需要 SSH 密钥或 token

***

## 参考文档

* 详细故障记录: `references/hc-project-sync-failure-2026-08-01.md`
* 项目档案: `/opt/hc-project/PROJECT_REGISTRY.md`

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
