---
name: book-to-skill
description: 把文档(PDF/EPUB/DOCX/HTML/MD/RTF/MOBI)转为Agent Skill
version: 1.0.0
category: imported
tags: []
metadata:
  hermes:
    tags: []
    source: IMA 知识库导入
---

# book-to-skill

> 把文档(PDF/EPUB/DOCX/HTML/MD/RTF/MOBI)转为Agent Skill。提取框架/心智模型/原则/技法/反模式。当需要'转技能/知识库/学一本书/提取框架'时触发。

# Book-to-Skill Converter

Transform written knowledge into actionable agent skills by extracting structure — not producing summaries.

## Philosophy

Books contain crystallized expertise: frameworks, principles, and techniques that took years to develop. This skill extracts that knowledge into a format GitHub Copilot CLI, Amp, Claude Code, or another compatible agent can leverage repeatedly.

**Extract structure, not summaries.** A skill isn't a book report. It's a toolkit of:

* Named frameworks (mental models with clear application)
* Actionable principles (rules that guide decisions)
* Techniques (step-by-step methods)
* Anti-patterns (what to avoid and why)
* Voice calibration (how the author thinks and communicates)

**Preserve the author's precision.** Frameworks often have specific names for reasons. "The 5 Whys" isn't interchangeable with "ask why multiple times." Capture the exact formulation.

**Layer depth appropriately.** Simple books → simple skills. Complex books with 10+ frameworks → skills with reference files and on-demand chapters.

***

## Modes of Operation

Four paths available. Route based on what the user asks:

### 1. Full Conversion (Default)

**Trigger:** User provides one or more document/directory/glob paths without special instructions

**Action:** Run all steps below (Steps 0–9)

**Output:** Complete skill with SKILL.md, chapters/, glossary, patterns, cheatsheet

### 2. Analyze Only

**Trigger:** User says "analyze", "just extract", or "I want to review before generating"

**Action:** Run Steps 0–3, then produce a structured extraction report (frameworks, principles, techniques found). Stop — do NOT generate skill files.

**Output:** Analysis report for user review

### 3. Generate from Prior Analysis

**Trigger:** User has existing analysis notes or previously ran analyze-only

**Action:** Skip Steps 0–3, use the provided analysis as input, run Steps 4–9

**Output:** Skill files from the provided analysis

### 4. Update / Fold-in (Existing Skill)

**Trigger:** User provides one or more new source paths and indicates they want to update an existing skill (either by pointing to the existing skill folder, providing a skill slug that already exists in `SKILLS_HOME`, or explicitly requesting an update).

**Action:** Run Step 0 (out-of-scope check), Step 1 (validate inputs), Step 1.5 (identify book type), and Step 2 (extract new files). Then skip to Step 5 (identify/detect existing skill path) and run the **Update / Fold-in Workflow** to merge the new content into the existing skill files.

**Output:** Updated existing skill with new/revised chapter summaries and merged indexes/glossaries.

***

## Skill Locations

This converter can run from multiple skill systems. When looking for this converter's helper script or writing the generated book skill, prefer these locations in order:

1. GitHub Copilot CLI personal skills: `~/.copilot/skills/`
2. Cross-agent personal skills (Copilot + Amp): `~/.agents/skills/`
3. Claude Code personal skills: `~/.claude/skills/`
4. Project-local Copilot skills: `.github/skills/`
5. Project-local Claude skills: `.claude/skills/`
6. Project-local Amp / Copilot skills: `.agents/skills/`
7. Amp global skills: `~/.config/agents/skills/`
8. Amp legacy global skills: `~/.config/amp/skills/`

For **generated** book skills, pick a destination that the user's host agent can actually discover (see Step 5). When more than one valid root exists, ask the user once and remember the answer for the session — do not silently default.

***

## Step 0 — Out-of-scope check

If no arguments are provided, stop and respond:

> "book-to-skill requires a supported document path, folder, or glob pattern. Usage: `book-to-skill <path-to-document-folder-or-glob>... [skill-name-slug]`"

Throughout the workflow:

* Identify the input paths and the optional skill slug.
* If the last argument is not a file, folder, or glob that exists or matches any files, and it looks like a skill slug (e.g. lowercase hyphens, alphanumeric), treat it as `SKILL_NAME`.
* Treat all other arguments as the list of `INPUT_PATHS`.
* If any input path is an existing skill directory (contains `SKILL.md` and

## 触发条件

把文档(PDF/EPUB/DOCX/HTML/MD/RTF/MOBI)转为Agent Skill。提取框架/心智模型/原则/技法/反模式。当需要'转技能/知识库/学一本书/提取框架'时触发。
## 验证

- [ ] 按上述步骤执行成功
- [ ] 输出符合预期，无报错
