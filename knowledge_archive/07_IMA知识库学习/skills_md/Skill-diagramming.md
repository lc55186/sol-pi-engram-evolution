# Skill-diagramming

***

name: diagramming
description: Diagram creation skills for generating visual diagrams, flowcharts, architecture diagrams, and illustrations.
--------------------------------------------------------------------------------------------------------------------------

# Diagramming — 图表绘制技能

## 概述

图表绘制技能包，支持流程图、架构图、插图等可视化图表生成。

## 输出格式决策树

| **需求**          | **推荐格式**           | **引用**                                                 |
| --------------- | ------------------ | ------------------------------------------------------ |
| 快速理解流程/架构       | Markdown + Mermaid | 对话内直接渲染                                                |
| 正式可交付报告/信息图     | **HTML（单文件零依赖）**   | 见 <br/>[html-delivery.md](references/html-delivery.md) |
| 演示文稿            | PPTX（导出）           | officecli skill                                        |
| 可交互探索（拖拽/折叠/切换） | HTML + JS          | 见 Effective HTML 原则                                    |

## HTML 交付物生成规范

当用户要求生成 HTML/信息图/报告时，遵循以下流程：

1. **检查 DESIGN.md** — 工作目录若有 `DESIGN.md`，读取其变量系统（颜色/字体/间距），不硬编码
2. **单文件原则** — 所有 CSS/JS 内联，零外部依赖（无 CDN、无 Google Fonts、无外部图片）
3. **暗色模式** — 必须支持 `data-theme` 切换，按钮固定右上角，状态存 localStorage，无闪白屏
4. **归档位置** — 输出到 `workspace/reports/artifacts/topic-YYYY-MM-DD.html`
5. **验证** — 浏览器直接打开能工作，无需 `npm install` 或构建步骤

## 步骤

1. **明确查询目标** — 确认要查找的信息
2. **检索相关内容** — 从知识库/文档中检索
3. **整理输出** — 结构化呈现结果
4. **标注来源** — 引用原始出处

## 验证

- [ ] 检索结果与查询目标相关

- [ ] 信息准确且最新

- [ ] 来源可追溯
