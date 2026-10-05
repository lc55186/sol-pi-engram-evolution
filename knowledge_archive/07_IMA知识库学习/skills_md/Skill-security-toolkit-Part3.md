# Skill-security-toolkit-Part3

8090 --set-target=DROP

firewall-cmd --reload

# rc.local 备份（防止 firewalld 不持久化）

echo "iptables -I INPUT -s 45.148.10.0/24 -j DROP -m comment --comment 'AS48090'" >> /etc/rc.local

chmod +x /etc/rc.local

````

验证：`iptables -L INPUT -n -v | grep AS48090`

### 被动SSH蜜罐

蜜罐设计原则：**只记录，不反击**。

```bash
# 开放蜜罐端口（firewalld）
firewall-cmd --permanent --add-port=22222/tcp
firewall-cmd --reload

# 启动蜜罐（见 scripts/honeyport_ssh.py）
python3 scripts/honeyport_ssh.py &

# systemd 托管（崩溃自恢复）
systemctl enable --now honeyport-ssh
````

蜜罐数据目录：

* `/var/log/honeyport/sessions/*.json` — 每次会话完整记录（IP、尝试用户名/密码、执行命令）
* `/var/log/honeyport/iocs.json` — 提取的IOC汇总（时间线、攻击者画像）

Cron自动化：每6小时分析蜜罐数据 → 统计攻击IP/密码/C2命令 → 自动封禁新IP → 清空已处理日志。

### Pitfalls

* **不要**在蜜罐中放置真实敏感文件 — 攻击者可能利用它们作为证据
* **不要**伪造过于真实的SSH密钥 — 保持"可信但可疑"的平衡
* **AS封禁前**确认ASN归属 — 避免误伤正常业务
* **蜜罐端口**必须通过firewalld放行 — iptables规则不自动开放端口
* **系统服务**用systemd托管，不要用nohup/后台进程 — 崩溃后无法自恢复

## 依赖

* bash 4.0+
* jq（JSON 输出）
* kubectl + jq（K8s 审计，可选）
* Python 3.10+（SOAR 编排器，标准库 sqlite3/subprocess/dataclasses）
* Docker CLI（容器隔离动作，可选）
* iptables（IP 封锁动作，需 root）

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
