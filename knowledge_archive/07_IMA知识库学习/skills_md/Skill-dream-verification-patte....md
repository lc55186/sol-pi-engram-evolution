# Skill-dream-verification-pattern

***

name: dream-verification-pattern
description: |
幻觉疫苗修复验证流程：当梦境系统发现 MEMORY.md 与实际配置不一致时，
使用验证脚本确认修复结果。验证脚本写在 /tmp/ 后执行，清理临时文件。
触发词：幻觉疫苗 / MEMORY.md 修正 / 梦境验证
version: 1.0.0
category: devops
tags: \[dreaming, verification, memory-md]
related\_skills: \[hermes-dreaming, session-maintenance, idle-conservation-workflow]
------------------------------------------------------------------------------------

# 梦境验证模式

## 触发场景

当 **幻觉疫苗**（dream-keeper handler.py 或 Agent 手动执行）发现以下不一致时：

| **不一致类型** | **示例**                                                             |
| --------- | ------------------------------------------------------------------ |
| 模型名称      | MEMORY.md 写 LongCat，实际是 agnes-2.0-flash                            |
| 归档日期      | MEMORY.md 归档于 2026-07-25，实际 2026-08-09                             |
| 配置路径      | MEMORY.md 写 \~/.hermes/memories/MEMORY.md，实际在 \~/.hermes/MEMORY.md |
| 磁盘使用率     | dream\_state.json 写 94%，实际 84%                                     |

## 验证流程

### 步骤 1: 编写验证脚本（/tmp/）

```python
#!/usr/bin/env python3
"""验证梦境修正结果"""
import json
import os

def verify():
    errors = []
    
    # 1. 检查梦境日志
    dream_path = "/root/.hermes/logs/dreaming/dream_YYYYMMDD_HHMMSS.json"
    if os.path.exists(dream_path):
        with open(dream_path) as f:
            dream = json.load(f)
        assert dream["trigger"] == "scheduled"
        assert len(dream["dimensions"]["preference"]) == 3
        print(f"✅ Dream log: {dream_path} ({os.path.getsize(dream_path)} bytes)")
    else:
        errors.append(f"❌ Dream log missing: {dream_path}")
    
    # 2. 检查 dream_state.json
    state_path = "/root/.hermes/dream_state.json"
    with open(state_path) as f:
        state = json.load(f)
    assert state["total_dreams"] >= 60  # 递增检查
    print(f"✅ Dream state: total_dreams={state['total_dreams']}")
    
    # 3. 检查 MEMORY.md 修正
    with open("/root/.hermes/MEMORY.md") as f:
        lines = f.readlines()
    
    # 验证关键行（按索引检查）
    # line 4 (index 3): 架构行
    assert "LongCat" not in lines[3], "Line 4 still has LongCat"
    assert "agnes-2.0-flash" in lines[3], "Line 4 missing agnes-2.0-flash"
    
    # line 11 (index 10): 主力模型行
    assert "LongCat" not in lines[10], "Line 11 still has LongCat"
    assert "agnes-2.0-flash" in lines[10], "Line 11 missing agnes-2.0-flash"
    
    # 归档日期
    assert "2026-08-09" in "".join(lines), "Date not updated"
    
    print("✅ MEMORY.md: model names corrected, date updated")
    
    # 4. 清理
    os.remove(__file__)
    print("\n✅ All verifications passed!")

if __name__ == "__main__":
    verify()
```

### 步骤 2: 执行验证

```bash
python3 /tmp/verify-dream-20260809.py
```

### 步骤 3: 清理临时文件

```bash
rm /tmp/verify-dream-*.py
```

## Pitfalls

1. **验证脚本必须写 /tmp/**：不要写到项目目录，避免污染
2. **用 read\_file 验证关键行**：确认 patch 后实际内容正确
3. **dream\_state.json 计数器检查**：total\_dreams 应该递增，不是固定值
4. **MEMORY.md 行号可能变化**：用索引 + 内容双重验证，不要只依赖行号

## Cron 环境约束

| **工具**                     | **可用性**    | **说明**                          |
| -------------------------- | ---------- | ------------------------------- |
| `memory`                   | ❌ DISABLED | 用 patch 替代                      |
| `execute_code`             | ❌ BLOCKED  | 用 terminal + python3 -c 或 patch |
| `patch`                    | ✅ 可用       | 首选文件修改工具                        |
| `read_file` / `write_file` | ✅ 可用       | 验证和写入                           |

## 版本历史

* v1.0.0 (2026-08-09): 初始版本，从梦境巩固会话提取
