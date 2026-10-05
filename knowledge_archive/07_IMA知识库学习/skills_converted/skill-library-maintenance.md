---
name: skill-library-maintenance
description: 维护 Hermes Skill 库完整性：检查双目录结构、补充缺失 frontmatter、运行 Curator 清理
version: 1.0.0
category: devops
tags: ["skill", "maintenance", "audit", "curator"]
metadata:
  hermes:
    tags: ["skill", "maintenance", "audit", "curator"]
    source: IMA 知识库导入
---

# skill-library-maintenance

> 维护 Hermes Skill 库完整性：检查双目录结构、补充缺失 frontmatter、运行 Curator 清理。触发词：skill 审计 / 技能库维护 / 检查 skill / 修复 skill 路径 / 清理归档

# Skill 库维护

## When to Use

* 需要检查 Skill 库完整性
* Skill 工具报 "Skill not found" 但文件存在
* 需要清理过期/重复 Skill
* 每月定期健康检查
* IMA上传内容安全校验

## 问题识别

### 1. 双目录结构（常见根因）

```
/root/.hermes/skills/           ← 根目录（官方标准）
/root/.hermes/skills/skills/    ← 嵌套目录（冗余）
```

**症状**：`skill_manage(action='patch', name='xxx')` 报 "Skill not found"

**诊断命令**：

```bash
# 统计 SKILL.md 文件数
find /root/.hermes/skills/ -name 'SKILL.md' | wc -l
find /root/.hermes/skills/ -name 'SKILL.md' -exec grep -q "^name:" {} \; | wc -l

# 检查双目录重复
for d in /root/.hermes/skills/*/; do
  name=$(basename "$d")
  [ -d "/root/.hermes/skills/skills/$name" ] && echo "DUPLICATE: $name"
done
```

### 2. 缺少 frontmatter 的 SKILL.md

```bash
# 找出缺少 name 字段的文件
find /root/.hermes/skills/ -name 'SKILL.md' ! -exec grep -q "^name:" {} \; -print
```

### 3. Skill SOP 合规检查（2026-08-03 新增）

**问题**：47个Skill缺少"步骤"章节，27个缺少"验证"章节

**解决方案**：

```bash
python3 /root/.hermes/scripts/fix_skill_sop.py
```

**分类规则**：

| **类别**    | **关键词**           | **步骤模板**         |
| --------- | ----------------- | ---------------- |
| workflow  | 转换/生成/创建/部署/分析    | 4步：准备→执行→输出→异常   |
| reference | 参考/查询/文档/lookup   | 4步：明确目标→检索→整理→标注 |
| config    | 配置/设置/maintenance | 4步：读取→应用→验证→回滚   |
| generic   | 其他                | 3步：接收→执行→返回      |

**当前状态**：98.7% 合规（75/76），仅1个待修复

### 4. 脚本去重检查（2026-08-03 新增）

**问题**：82个脚本中存在重复功能，占用磁盘空间

**解决方案**：

```bash
# 统计脚本总数
ls /root/.hermes/scripts/*.py | wc -l
# 检查冗余入口
ls /root/.hermes/scripts/unified_*.py 2>/dev/null | wc -l
```

**已合并**：

* `evaluation_dashboard.py` + `evolution_dashboard.py` → `unified_dashboard.py`
* `agent_shield.py` + `security_auditor.py` + `skill_security_scanner.py` → `unified_security.py`

**当前状态**：65脚本（↓20.7%）

### 5. 归档状态

```bash
find /root/.hermes/skills/skills/.archive/ -name 'SKILL.md' | wc -l
find /root/.hermes/skills/skills/.archive/expired/ -name 'SKILL.md' | wc -l
```

## 修复流程

### 步骤 1：补充缺失 frontmatter

对每个缺少 `name:` 的 SKILL.md，添加：

```yaml
---
name: <skill-name>
description: <一句话描述>
version: 1.0.0
metadata:
  hermes:
    tags: [tag1, tag2]
    category: <category>
---
```

### 步骤 2：统一目录结构

**推荐**：保留根目录版本，删除嵌套版本

```bash
# 确认根目录版本完整后删除嵌套
rm -rf /root/.hermes/skills/skills/<skill-name>/
```

### 步骤 3：运行 Curator 清理

```bash
hermes curator run --consolidate  # 合并重叠 Skill
hermes curator prune              # 清理过期归档
hermes curator backup             # 创建备份
```

## 已知问题修复记录

* **2026-08-01**: 发现双目录结构问题（根目录 31 子目录 vs 嵌套 61 子目录），5 个 SKILL.md 缺少 name frontmatter（已修复：firecrawl/ima/notes/java-core/python-core），sqlite3 CLI 缺失
* **2026-08-01**: weiyun\_backup.py profiles 目录压缩超时修复（120s→300s）
* **2026-08-01**: 嵌套目录 `/root/.hermes/skills/skills/` 仍有 61 个 skill 未合并到根目录，需手动执行目录合并（见下方双目录清理步骤）
* **2026-08-03**: Skill SOP 批量修复，75/76 合规（98.7%）
* **2026-08-03**: 脚本去重，82→65（↓20.7%），新增 unified\_dashboard.py 和 unified\_security.py
* **2026-08-03**: IMA上传安全约束 — tirith扫描拦截smart quotes/em-dash，内容必须用ASCII字符
* **2026-08-10**: MEMORY-Skill 同步检查 — 发现 4 个 Skill 记录缺口（content-authentication/index-browser-agent/idle-conservation-workflow/system-health-dashboard）

### 步骤 1.5：补充缺失 name frontmatter（2026-08-01 新增流程）

对缺少 `name:` 的 SKILL.md，在文件头部添加：

```yaml
---
name: <skill-name-from-directory>
description: "<一句话描述>"
category: <category-from-parent-dir>
tags: [tag1, tag2]
---
```

**验证**：`find /root/.hermes/skills/ -name 'SKILL.md' ! -exec grep -q "^name:" {} \; -print` 应返回 0

**已修复案例**（2026-08-01）：

* `skills/devops/firecrawl/SKILL.md` → name: firecrawl
* `skills/ima/ima-skill/knowledge-base/SKILL.md` → name: knowledge-base
* `skills/ima/ima-skill/notes/SKILL.md` → name: notes
* `skills/java-core/SKILL.md` → name: java-core
* `skills/python-core/SKILL.md` → name: python-core

### 步骤 1.6：MEMORY-Skill 同步检查（2026-08-10 新增）

**问题**：活跃 Skill 数（51个）与 MEMORY.md 记录的 Skill 数（47个）存在 4 个缺口，导致 MEMORY 无法作为准确索引。

**诊断命令**：

```bash
# 1. 统计活跃 Skill 数（排除 .archive）
find /root/.hermes/skills -name SKILL.md -not -path '*/.archive/*' | wc -l

# 2. 统计 MEMORY 中记录的 Skill
grep -oP '[-*] $\w[^$]*\]' ~/.hermes/MEMORY.md | wc -l

# 3. 找出 MEMORY 中缺失的 Skill（对比目录名与 MEMORY 索引）
for d in /root/.hermes/skills/*/; do
  name=$(basename "$d")
  if ! grep -q "$name" ~/.hermes/MEMORY.md; then
    echo "MISSING: $name"
  fi
done
```

**修复**：将缺失的 Skill 以 `[skill-name] 一句话描述 | -> references/xxx.md` 格式补充到 MEMORY.md 对应类别下。

## Pitfalls

* **不要手动 mkdir + write\_file 创建 Skill**：始终用 `skill_manage(action='create')`
* **双路径问题**：`skill_view` 显示 `skill_dir` 包含双 `skills` 路径时，说明文件在嵌套目录中
* **Curator 不自动修复路径**：只处理归档和合并，不解决双目录问题
* **sqlite3 CLI 缺失**：系统未安装，用 `python3 /root/.hermes/scripts/sqlite_query.py` 替代
* **cron-reliability 是手动创建 skill**：无法通过 skill\_manage 修改，需手动编辑 SKILL.md 文件
* **脚本去重优先于删除**：合并脚本（如 unified\_\*.py）保留核心功能，比直接删除更完整
* **IMA上传必须ASCII**：tirith安全扫描拦截smart quotes/em-dash/变体选择符，所有外部上传内容改用ASCII字符（`" ' -- ...`），详见 references/ima-ascii-constraint-20260803.md
* \*\*多 profile 嵌套


