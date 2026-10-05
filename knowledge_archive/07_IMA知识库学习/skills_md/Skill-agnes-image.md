# Skill-agnes-image

***

name: agnes-image
description: AI 图片生成工具。通过 Agnes-Image-2.0-Flash 模型根据文本描述生成高质量图片。支持多种尺寸和风格。适用于：封面设计、文章配图、海报制作、电商主图、创意素材。
-------------------------------------------------------------------------------------------------------

# Agnes 图片生成 Skill

## 触发条件

用户请求生成图片、封面、海报、配图、插画时使用。

## 工具

### generate\_image

调用 Agnes Image 2.0 Flash API 生成图片。

```bash
curl -s -X POST 'https://apihub.agnes-ai.com/v1/images/generations' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer sk-3TJ3PzAqsIjstcjBeMcPsm51F22jp2VCdMz08RJopE2PqzAM' \
  -d '{
    "model": "agnes-image-2.0-flash",
    "prompt": "<用户描述>",
    "n": 1,
    "size": "<尺寸>"
  }'
```

### 参数说明

| **参数**   | **默认值**     | **可选值**                                               |
| -------- | ----------- | ----------------------------------------------------- |
| `prompt` | (必填)        | 英文提示词效果最佳                                             |
| `n`      | 1           | 1-4                                                   |
| `size`   | "1024x1024" | "1024x1024", "1024x1792"(竖版9:16), "1792x1024"(横版16:9) |

### 输出处理

1. API 返回 `data[0].url` 包含图片链接
2. 下载图片保存到 `/tmp/agnes-images/` 目录
3. 用 `MEDIA:<path>` 发送给用户

## 提示词工程规则

1. **英文优先**：英文出图效果更好
2. **具体描述**：包含主体、风格、光影、色调、质量关键词
3. **质量后缀**：追加 `cinematic lighting, 4K quality, highly detailed, professional photography`
4. **风格关键词**：
   * 科技感：`futuristic, cyberpunk, neon, holographic`
   * 商务：`corporate, professional, clean, minimalist`
   * 中国风：`traditional Chinese, ink painting, elegant`
   * 插画：`digital art, illustration, vibrant colors`

## 工作流

```
1. 接收用户描述（中文需翻译为英文）
2. 构建高质量 prompt（添加风格/质量关键词）
3. 调用 API 生成
4. 下载图片到 /tmp/agnes-images/
5. 发送给用户（MEDIA: 方式）
6. 简短确认
```

## 注意事项

* 免费 API，无需担心成本
* 生成时间约 5-15 秒
* 图片 URL 有时效性，需立即下载
* **Google Storage 下载可能超时**：curl 直连 storage.googleapis.com 不稳定，用 `wget -q --timeout=30` 更可靠
* **大尺寸图片（1792x1024）** 比正方形（1024x1024）生成更慢，约 30-60 秒

## 参考文件

* `references/api_reference.md` — API 参数、返回格式、风格关键词速查
* `references/2026-06-03_test_session.md` — 真实测试记录（Google Storage 超时、大尺寸图片慢、邮件发送方式）
* `references/hermes-plugin-integration.md` — Hermes 插件架构指南（目录结构、注册模式、save\_url\_video 坑、测试方法）

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
