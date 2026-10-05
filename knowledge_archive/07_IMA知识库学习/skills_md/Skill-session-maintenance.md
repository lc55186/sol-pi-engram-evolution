# Skill-session-maintenance

***

name: session-maintenance
description: "Hermes 会话管理：状态.db 归档、清理、健康检查。当需要归档会话、清理 state.db、或处理活跃会话超阈值时加载。"
category: devops
tags: \[session, archive, state-db, maintenance]
------------------------------------------------

# 会话维护

## 核心原则

1. **归档优先**：系统会话（cron/api/tui）和低消息会话优先归档
2. **分批执行**：每次归档 50-100 个，避免超时
3. **循环归档**：单次阈值不够，需循环直到低于目标
4. **VACUUM 手动**：大库（>400MB）VACUUM 会超时，需手动在空闲时执行

## 会话归档流程

### 检查状态

```python
import sqlite3
conn = sqlite3.connect('/root/.hermes/state.db')
cur = conn.cursor()
cur.execute('SELECT count(*) FROM sessions WHERE archived = 0')
active = cur.fetchone()[0]
cur.execute('SELECT count(*) FROM sessions WHERE archived = 1')
archived = cur.fetchone()[0]
print(f'活跃: {active}, 已归档: {archived}')
```

### 归档低消息系统会话（2026-08-13 优化：孤立会话优先）

**2026-08-13 发现**：孤立 cron 会话（`user_id IS NULL`）是最有效的归档目标，无需限制 message\_count。

```python
# 第一步：优先归档孤立 cron 会话（user_id IS NULL AND >7天）
cur.execute("""
    UPDATE sessions SET archived = 1 WHERE id IN (
        SELECT id FROM sessions WHERE archived = 0
        AND user_id IS NULL
        AND source = 'cron'
        AND started_at < datetime('now', '-7 days')
        ORDER BY started_at ASC LIMIT 200
    )
""")
conn.commit()
print(f'归档孤立会话: {cur.rowcount}')

# 第二步：验证后继续低消息归档（如需）
cur.execute('SELECT count(*) FROM sessions WHERE archived = 0')
active = cur.fetchone()[0]
```

**实测效果**：51 个孤立 cron 会话归档，活跃从 53 → 2。

### 循环归档直到阈值以下（2026-08-03 更新）

**重要发现**：单次归档不够，需循环执行，每次放宽条件：

```python
# 第一轮：msg <= 5，归档19个（339→320）
cur.execute("""
    UPDATE sessions SET archived = 1 WHERE id IN (
        SELECT id FROM sessions WHERE archived = 0
        AND source IN ('cron', 'api_server', 'tui')
        AND message_count <= 5
        ORDER BY started_at ASC LIMIT 50
    )
""")
conn.commit()

# 验证后继续
cur.execute('SELECT count(*) FROM sessions WHERE archived = 0')
active = cur.fetchone()[0]

# 第二轮：放宽到 msg <= 6，归档46个（320→274）
if active > 300:
    cur.execute("""
        UPDATE sessions SET archived = 1 WHERE id IN (
            SELECT id FROM sessions WHERE archived = 0
            AND source IN ('cron', 'api_server', 'tui')
            AND message_count <= 6
            ORDER BY started_at ASC LIMIT 50
        )
    """)
    conn.commit()

# 继续直到低于阈值300
```

**实测数据**：

| **轮次** | **条件**    | **归档数** | **剩余活跃** |
| ------ | --------- | ------- | -------- |
| 1      | msg \<= 5 | 19      | 339→320  |
| 2      | msg \<= 6 | 46      | 320→274  |
| 3      | 停止（低于300） | -       | 274      |

## 归档工作流示例（2026-08-01/2026-08-03）

**场景**：Cron 报告活跃会话 751 > 300 阈值

**执行步骤**：

1. 第一批归档 600 个低消息系统会话（message\_count ≤ 5）
2. 验证后剩余 339，继续归档 50 个（放宽到 message\_count ≤ 6）
3. 最终活跃会话：274（低于 300 阈值）

**结果**：

| **指标** | **归档前** | **归档后** |
| ------ | ------- | ------- |
| 活跃会话   | 751     | 274     |
| 已归档    | 849     | 1415    |
| 归档数量   | —       | 566     |

## Pitfalls

1. **MEMORY.md 底部累积旧报告**：梦境报告等历史条目会沉底堆积（如7月梦境报告），占用7KB+配额且无当前价值。定期清理底部旧报告，只保留顶部精简版索引
2. **VACUUM 超时**：400MB+ 数据库 VACUUM 会超时，不要自动触发
3. **孤立会话优先归档**：`user_id IS NULL AND source='cron'` 的会话归档效率最高（2026-08-13实测：51个孤立会话→活跃从53降至2）
4. **归档不可逆**：确认后再执行
5. **message\_count 定义**：`<=5` 表示几乎无内容的会话
6. **单次归档不够**：需循环执行，每次放宽阈值
7. **FTS存储版本**：v23布局下，删除消息行比VACUUM更有效
8. **VACUUM效果有限**：482.6MB→479.5MB仅-3.1MB，属结构性占用正常
9. **state.db 深度清理未实现**：2026-08-03 发现 VACUUM 对 FTSv23 几乎无效，需执行 `DELETE FROM messages WHERE session_id IN (SELECT id FROM sessions WHERE archived=1)`
10. **孤立会话归档优先**：`user_id IS NULL AND source='cron'` 的会话即使消息数>5也应归档，这是最高效的清理策略（2026-08-13）
11. **profile state.db 膨胀**：2026-08-04 发现 coder/scout profile 的 state.db 各达 888MB，合计 2.6GB。建议评估双分身必要性，或定期清理非 default profile 的会话
12. **MEMORY.md 使用率接近上限**：2026-08-06 达到 93%（7,509/8,000 bytes），需定期清理过时条目
13. **数据库损坏恢复**：2026-08-13 state.db 严重损坏（FTS5+messages损坏），采用空数据库重建方案。详见"数据库损坏恢复"章节

## 深度清理流程（FTSv23 适用，2026-08-06 更新）

**2026-08-06 实测关键发现**：

* 归档 134 个 >30d 会话后，VACUUM 仅减 3MB（511→508MB）
* freelist 从 73 页降至 0.1MB，页已释放但 FTS 内容未清除
* **结论**：VACUUM 无法清理 FTSv23 索引，必须 DELETE FROM messages

**深度清理 SQL**（需人工确认后再执行）：

```sql
-- 1. 统计待删除消息数
SELECT COUNT(*) FROM messages WHERE session_id IN (SELECT id FROM sessions WHERE archived = 1);

-- 2. 删除已归档会话的消息（关键步骤，不可逆）
DELETE FROM messages WHERE session_id IN (SELECT id FROM sessions WHERE archived = 1);

-- 3. VACUUM 释放空间
VACUUM;
```

**预期效果**：删除 31,243 条归档会话消息后，state.db 从 \~508MB 降至 \~300-350MB。

**安全警告**：此操作不可逆，删除后归档会话消息无法通过 FTS 检索。

**预防**：备份前先验证备份数据库可读性，避免"备份也无法恢复"的情况。

## 健康阈值

| **指标**               | **阈值**              |
| -------------------- | ------------------- |
| 活跃会话                 | ≤ 300               |
| 已归档                  | > 800（建议）           |
| state.db 大小          | \< 500MB            |
| profiles/\*/state.db | \< 500MB（单 profile） |

**新增风险（2026-08-04）**：

* coder/scout profile 的 state.db 均达 888MB，合计 2.6GB
* 建议评估双分身必要性，或定期清理非 default profile 的会话
* `references/state-db-broken-20260813.md` — state.db 严重损坏修复案例（FTS5+messages损坏）

## 脚本

* `scripts/fix-state-db.py` — 数据库损坏时重建空数据库的最后手段
* `cron-reliability` skill — cron 任务可靠性保障
* `references/archive-multi-round-20260803.md` — 多轮归档实测数据（339→320→274）
* `references/fts-v23-cleanup-verification-20260806.md` — VACUUM 对 FTSv23 无效的验证与深度清理方案
* `references/isolated-cron-sessions-20260813.md` — 孤立 cron 会话归档策略（51个会话归档示例）
* `references/weekly-evolution-audit-20260813.md` — 本周自进化审计报告（12个新Skill，冗余风险评估）

## 步骤

1. \*\*接收输入
