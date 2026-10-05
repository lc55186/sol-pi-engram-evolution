# Skill-markitdown

***

name: markitdown
description: 文档格式转换工具。将 PDF/DOCX/PPTX/XLSX/HTML/CSV/JSON/XML/EPub/图片/音频/YouTube 转换为 Markdown 格式。当需要读取和分析非文本文件时激活。
trigger: 文件转换 / PDF转Markdown / Word转Markdown / PPT转Markdown / 文档解析 / markitdown / file convert
----------------------------------------------------------------------------------------------

# MarkItDown 文档转换

## 概述

微软出品的文档转 Markdown 工具（145K+ stars, MIT 协议），支持 15+ 格式。

## 安装

```bash
# 最小安装（推荐，避免 torch 编译超时）
pip install 'markitdown[pdf,docx,pptx]' --no-deps

# 完整安装（含图片 OCR、音频转写等 ML 功能）
pip install markitdown  # 会拉 torch 等大依赖，编译可能超时
```

已安装版本：0.1.6（最小安装）

## 使用方式

### Python API

```python
from markitdown import MarkItDown

md = MarkItDown()

# 转换文件
result = md.convert("document.pdf")
print(result.text_content)  # Markdown 文本

# 转换多个文件
for path in ["a.pdf", "b.docx", "c.pptx"]:
    result = md.convert(path)
    with open(f"{path}.md", "w") as f:
        f.write(result.text_content)
```

### 命令行

```bash
markitdown document.pdf > output.md
markitdown document.docx > output.md
```

### 在 Hermes 中使用

当需要读取非文本文件时：

```python
from markitdown import MarkItDown

md = MarkItDown()

# 1. 转换文件
result = md.convert("/path/to/file.pdf")

# 2. 将 Markdown 内容用于后续分析
content = result.text_content
```

## 支持的格式

| **格式**     | **扩展名**         | **说明**             |
| ---------- | --------------- | ------------------ |
| PDF        | .pdf            | 含表格、公式、图片          |
| Word       | .docx           | 含格式、表格、批注          |
| PowerPoint | .pptx           | 含布局、备注             |
| Excel      | .xlsx           | 含公式、多 Sheet        |
| HTML       | .html           | 转纯 Markdown        |
| CSV        | .csv            | 转 Markdown 表格      |
| JSON       | .json           | 格式化输出              |
| XML        | .xml            | 结构化输出              |
| EPub       | .epub           | 电子书                |
| 图片         | .jpg/.png/.webp | OCR 文字识别（需 LLM 增强） |
| 音频         | .mp3/.wav       | 语音转文字（需 LLM 增强）    |
| YouTube    | URL             | 提取字幕               |

## LLM 增强模式

可选：用 LLM 增强图片描述、OCR、表格理解。

```python
from markitdown import MarkItDown
from openai import OpenAI

md = MarkItDown(
    llm_client=OpenAI(),
    llm_model="gpt-4o",
)
result = md.convert("image.png")  # LLM 生成图片描述
```

## 注意事项

* 首次 import 约 2.6s（加载依赖），后续调用秒级
* 大文件（>100MB）可能较慢，建议分片处理
* 图片 OCR 和音频转写需要额外配置 LLM 客户端
* 默认配置已满足大多数场景，无需额外依赖
* **最小安装**（`--no-deps`）已足够大多数文档转换场景
* 完整安装会拉 torch 等 ML 依赖，在受限环境可能编译超时

## 替代方案：MinerU

当 markitdown 转换质量不佳（Office 文件表格复杂、结构丢失）时，用 MinerU：

```bash
# 安装
pip3 install mineru

# 转换 Office 文件
mineru -p document.docx -o /tmp/output
# 输出在 /tmp/output/<文件名>/office/<文件名>.md
```

**优势**：表格保留为 HTML table 格式、层级结构更准确、支持 batch 处理

**劣势**：首次运行会启动 FastAPI 服务（\~3s 启动），需要更多内存

## 参考文件

* `scripts/markitdown_cli.py` — 命令行接口脚本（支持批量转换）

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
