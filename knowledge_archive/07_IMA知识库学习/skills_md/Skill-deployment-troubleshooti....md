# Skill-deployment-troubleshooting

***

name: deployment-troubleshooting
title: 应用部署与配置排查手册
description: 针对 Spring Boot/Java 应用在容器/受限环境部署后的启动失败、配置解析错误、JVM内存异常、凭证不一致等常见问题的排查方法，以及 Node.js/Express + PM2 部署中的路由别名、进程模式等典型问题。覆盖远程 SSH 服务审计、Git diff 安全审查（JWT/Filter）、多项目共享日志诊断。当用户需要部署 Java 应用、排查启动失败、处理 YAML 配置错误、分析 GC 异常、配置 PM2 进程管理、处理源码/编译产物丢失、执行远程服务健康检查时激活。
category: devops
tags: \[部署, 配置排查, Spring Boot, JVM调试, 启动失败, GC异常, YAML, 密码不匹配, PM2, Node.js, Express, Profile配置, 微服务架构, Valkey, Netty, SSH部署, 源码丢失, 恢复策略, 多项目架构, Java110, 前端架构, 演示模式诊断, Nginx配置]
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# 应用部署与配置排查手册

> 从 Spring Boot 应用远程部署实践中提炼，覆盖 YAML 配置解析、JVM 内存、分布式缓存序列化、凭证同步等典型问题。

## 适用场景

* Java/Spring Boot 应用启动失败，日志中无明确错误或错误信息模糊
* 应用启动后 CPU 持续 90%+ 伴随连续 GC
* Redis/Valkey 缓存数据格式与预期不符
* YAML/Properties 配置文件解析报错
* 远程环境凭证与代码仓库配置不一致

## 快速诊断流程

```bash
1. 确认服务进程存在 → ps aux | grep <PID/jar>
2. 查看启动端口     → ss -tlnp | grep <PORT>
3. 检查 JVM GC 状态  → jstat -gcutil <PID> 2000 3
   (若 S0=100% + M>99% = 无限 GC)
4. 查看启动日志最后 50 行 → tail -50 logs/stdout.log
5. 定位根因后修复而非仅重启
```

**辅助脚本**:\n- `scripts/query_valkey.py` — 无 redis-cli 时通过 TCP 协议查询 Valkey（支持 KEYS/SET/GET）\n- `scripts/fix-java-version.py` — 批量修改多模块 Maven 项目的 pom.xml Java 编译目标版本（用法: `python3 fix-java-version.py 1.8 11 /path/to/project`）\n- `scripts/fix_microcommunity_boot.py` — 修复 MicroCommunity 启动失败（fat JAR + persistence-api 冲突，用法: `python3 fix_microcommunity_boot.py`）

* `references/java110-login-verification-pattern-2026-07-01.md` — 两套登录入口（/app/loginOwner vs /callComponent/login/doLogin）、验证码机制、日志路径陷阱、多进程冲突
* `references/hc-frontend-deployment-check-2026-07-01.md` — HC 社区前端部署状态检查（三种前端形态分类、演示模式诊断、Java110 路由差异）
* `references/node-pm2-remote-audit-pattern.md` — Node.js/PM2 远程部署快速巡检模式（单次 SSH 多命令检查链、判断标准、验证实例）
* `references/primary-school-chinese-deployment-2026-07-01.md` — 小学语文项目(47.114.124.212)部署巡检报告

## Node.js/PM2 部署陷阱

### PM2 cluster 模式与动态路由冲突

**现象**: Express 应用注册了 `app.all('/api/v1/*')` 等通配路由，但请求仍然 404 或返回静态文件

**根因**: cluster 模式下 Node.js 进程间负载均衡，中间件加载顺序在并发请求时不确定；SPA fallback (`express.static`) 与动态路由在 cluster 下偶发竞争

**修复**: 对中间件顺序敏感的 Express 应用，使用 `fork` 模式而非 `cluster`：

```javascript
// ecosystem.config.js
module.exports = {
  apps: [{
    name: 'app',
    script: 'server.js',
    exec_mode: 'fork',  // 不用 cluster
    instances: 1
  }]
}
```

### Node.js API 路由别名

**现象**: 前端调用的旧 API 路径 (`/api/v1/*`) 不再匹配当前路由注册

**修复**: 在路由文件末尾添加 307 重定向别名：

```javascript
app.all('/api/v1/user/*', (req, res) => {
  res.redirect(307, '/api/auth' + req.path);
});
app.all('/api/v1/*', (req, res) => {
  res.redirect(307, '/api/v2_0_0' + req.path);
});
```

**注意**: 确保别名路由注册在所有路由之后，避免拦截其他有效路由

## 远程Web服务SSH隧道测试

当无法直接访问远程服务器端口时，建立SSH隧道进行测试:

```bash
sshpass -p 'PASSWORD' ssh \
  -L <LOCAL_PORT>:127.0.0.1:<REMOTE_PORT> \
  -o StrictHostKeyChecking=no \
  -o ConnectTimeout=10 \
  user@<REMOTE_HOST> "sleep 360"
```

然后本地通过 `http://127.0.0.1:<LOCAL_PORT>` 访问远程服务。

**注意**: 保持SSH连接不断开（用 `&` 后台运行或另开终端）

### 1. YAML 重复键

**错误**: `IllegalStateException: duplicate key: spring`**原因**: 同一 YAML 文件中有两个同名顶层键（如两个 `spring:` 块）

**修复**: 保留第一个 `spring:`，后续子配置全部嵌套进该 `spring:` 块；用 `python3 -c "import yaml; yaml.safe_load(open('file.yml'))"` 验证

### 2. Redis 序列化格式不匹配

**错误**: `StreamCorruptedException: invalid stream header: <hex>`**原因**: 应用用 Java 原生序列化写 Redis，但手动插入的数据是 JSON

**修复**: 确保 Redis 缓存值始终是 Java serialized bytes；不要直接往 Redis 塞 JSON 字符串

### 3. JDK 16+ 缺少 `--add-opens`

**错误**: `InaccessibleObjectException: Unable to make ... accessible: module java.base does not "opens java.lang"`**原因**: Spring CGLIB 需要反射访问 JDK 内部类

**修复**: 启动命令中添加:

```bash
--add-opens java.base/java.lang=ALL-UNNAMED
--add-opens java.base/java.lang.reflect=ALL-UNNAMED
--add-opens java.base/java.util=ALL-UNNAMED
--add-opens java.base/java.io=ALL-UNNAMED
```

### 4. 凭证不一致导致 Metaspace 耗尽

**现象**: CPU 94%+，`jstat -gcutil` 显示 `S0=100%` + `Metaspace>99%`，进程 CPU 接近满分但无响应

**根因**: 缓存/数据库连接失败触发重试循环，每次重试加载新类元数据塞满 Metaspace

**修复**:

1. 确认应用配置中的密码与实际 Redis/DB 密码一致
2. 修正密码后重启
3. 建议 `-XX:MaxMetaspaceSize=256m`（默认 \~96MB 不够）

### 5. `--spring.profiles.active` 激活错误 profile

**现象**: 启动后发现使用了错误的数据库/环境配置

**根因**: `application-dev.yml` 有重复 `spring:` 键导致整个 dev profile 加载失败

**修复**: 临时去除 `--spring.profiles.active=dev` 让应用以默认 `application.yml` 启动绕过

### 6. JAR 内部 `application.yml` 覆盖外部配置

**现象**: 修改了 `application-dev.yml` 但启动仍报错或行为不符合预期

**根因**: 启动命令中包含 `loader.path=classpath:/`，导致 JAR 内部的 `application.yml`（旧版本）被加载并覆盖外部配置

**修复**: 同步更新 JAR 内的 `src/main/resources/application.yml`，或去掉 `classpath:/` loader 参数让外部配置优先

### 7. MicroCommunity AppRoute 缓存重建

**现象**: 登录接口返回 "鉴权失败：AppId 没有权限访问 serviceCode = xxx"

**根因**: Valkey 中的 AppRoute 缓存（Java 序列化格式）丢失或损坏

**修复**: 通过 API 触发缓存刷新：

```bash
curl "http://localhost:8008/api/v2_0_0/dev-service-cache/doFlushAppRoute"
```

**注意**: AppRoute 缓存使用 Java `ObjectOutputStream` 序列化，不是 JSON。不要试图手动写入 Redis。

### 8. 密码哈希验证（Double-MD5 + Salt）

**现象**: 使用明文密码登录失败，但数据库中存储的不是明文

**根因**: 部分 Java 应用使用 `MD5(MD5(password) + salt)` 双重哈希存储密码

**验证**: 用 Python 生成正确的哈希值后更新数据库：

```python
import hashlib
salt = "hc@java110"  # 应用特定 salt
password = "123456"
has
```
