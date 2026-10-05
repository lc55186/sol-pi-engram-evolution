# Skill-agnes-video

***

name: agnes-video
description: AI 视频生成工具。通过 Agnes-Video-V2.0 模型生成视频。支持文本转视频、图片转视频、多图合成、关键帧动画。适用于：短剧分镜、广告试拍、社交媒体内容、产品演示。
-----------------------------------------------------------------------------------------------------

# Agnes 视频生成 Skill

## 触发条件

用户请求生成视频、分镜、动画、短片时使用。

## 工具

### create\_video\_task

提交异步视频生成任务。

```bash
curl -s -X POST 'https://apihub.agnes-ai.com/v1/videos' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer sk-3TJ3PzAqsIjstcjBeMcPsm51F22jp2VCdMz08RJopE2PqzAM' \
  -d '{
    "model": "agnes-video-v2.0",
    "prompt": "<英文描述>",
    "height": 768,
    "width": 1152,
    "num_frames": 41,
    "frame_rate": 24
  }'
```

### get\_video\_result

查询任务状态和结果。

```bash
curl -s 'https://apihub.agnes-ai.com/v1/videos/<task_id>' \
  -H 'Authorization: Bearer sk-3TJ3PzAqsIjstcjBeMcPsm51F22jp2VCdMz08RJopE2PqzAM'
```

### 参数说明

| **参数**            | **默认值** | **说明**              |
| ----------------- | ------- | ------------------- |
| `prompt`          | (必填)    | 英文提示词               |
| `height`          | 768     | 视频高度                |
| `width`           | 1152    | 视频宽度                |
| `num_frames`      | 41      | 帧数，必须满足 8n+1，最大 441 |
| `frame_rate`      | 24      | FPS，1-60            |
| `image`           | -       | 图片 URL（图生视频时使用）     |
| `negative_prompt` | -       | 负面提示词               |

### 帧数与时长对照表

| **num\_frames** | **时长(24fps)** | **适用场景** |
| --------------- | ------------- | -------- |
| 41              | \~1.7秒        | 短片段/GIF  |
| 81              | \~3.4秒        | 短视频      |
| 121             | \~5秒          | 标准广告     |
| 241             | \~10秒         | 长片段      |

### 输出处理

1. 创建任务返回 `task_id`
2. 轮询状态直到 `status: "completed"`
3. 结果中包含视频 URL
4. 下载视频到 `/tmp/agnes-videos/`
5. 用 `MEDIA:<path>` 发送给用户

## 工作流

```
1. 接收用户描述（中文翻译为英文）
2. 构建高质量 prompt（添加 cinematic, dramatic lighting 等）
3. 提交任务，获取 task_id
4. 告知用户任务已提交
5. 每 10-15 秒轮询一次状态
6. 完成后下载视频并发送
```

## 提示词工程规则

1. **英文优先**：英文出视频效果更好
2. **分镜描述**：按时间段描述场景变化
3. **运镜关键词**：`pan left/right`, `zoom in/out`, `tracking shot`, `aerial view`
4. **质量后缀**：`cinematic quality, dramatic lighting, slow motion, 4K, photorealistic`
5. **竖版广告分镜**：9:16 竖版视频需明确 `height:1152, width:648`；prompt 用 `low angle tracking`、`shallow depth of field`、`spotlight` 等电影级镜头语言；**禁止**分镜框、字幕、海报排版等廉价短视频元素

## 注意事项

* 异步 API，**实际等待时间 3-15 分钟**（免费版排队严重，不是 30 秒）
* 结果字段是 `remixed_from_video_id`（不是 `result`/`outputs`/`url`）
* 免费 API，可大胆测试
* URL 有时效性，需立即下载
* **下载必须用 curl**：视频 CDN 域名是 `platform-outputs.agnes-ai.space`，`wget` 会返回空文件，`curl -L` 才能正确下载（实测 2.7MB 文件）
* **排队策略**：同时提交多个任务可提高命中率，先完成的先下载

## ⚠️ 避坑指南（2026-06-21 实战总结）

### 1. Prompt 长度限制 → 500 错误

* **现象**：复杂长 prompt（>300字符多场景描述）提交后进度到 30% 就报 `500 Internal generation failed`
* **根因**：免费版模型对长时序场景理解有限，生成中途崩溃
* **修复**：**精简 prompt**，聚焦单一场景/产品，控制在 150 字以内
  * ❌ 错误：多场景拼接（"Scene 1... Scene 2... Scene 3..."）
  * ✅ 正确：单一镜头描述（"A small white device on desk, glowing blue waves, person in background"）
* **降级方案**：如果精简 prompt 仍失败，进一步减少 `num_frames`（81→41）

### 2. 下载方式 & 代理绕过

* **CDN 域名** `platform-outputs.agnes-ai.space` 走代理（`$http_proxy` / `$https_proxy`）必被重置（curl exit code 35）

**必须直连**：`curl -L --noproxy '*'` — 实测 1.2\~2.2 MB 文件秒完成

```bash
# ✅ 正确 — 直连（--noproxy），实测 1.2~2.2MB 秒完成
curl -L --noproxy '*' -o /tmp/video.mp4 "https://platform-outputs.agnes-ai.space/videos/..." \
  -H "User-Agent: Mozilla/5.0" --connect-timeout 15 --max-time 120

# ❌ 错误 — 走代理 → 连接重置（curl exit code 35 / wget 0字节）
curl -L -o /tmp/video.mp4 "https://platform-outputs.agnes-ai.space/videos/..."
wget -q -O /tmp/video.mp4 "https://platform-outputs.agnes-ai.space/videos/..."
```

### 3. 免费版时长限制 & 速率限制

* 免费版单次最多 10 秒（241帧@24fps），实际常见 3-5 秒
* `seconds` 字段在提交时就确定，不是 max 而是实际分配
* **速率限制**：1 request/minute，连续提交会报 `rate_limit_exceeded`
* **分段制作策略**：需要 >10s 视频时，拆为数段（每段 \~5s / 121帧），间隔 60-90s 提交，然后 `ffmpeg -f concat -c copy` 拼接

```bash
# 例：三段拼接为 15s 竖版
echo "file '/tmp/part1.mp4'" > /tmp/concat.txt
echo "file '/tmp/part2.mp4'" >> /tmp/concat.txt
echo "file '/tmp/part3.mp4'" >> /tmp/concat.txt
ffmpeg -y -f concat -safe 0 -i /tmp/concat.txt -c copy /tmp/final.mp4
```

* FFmpeg h264 decoder 受限（`--disable-decoder=h264`），但 `-c copy`（stream copy）**不经过解码器**，能正常拼接
* 输出：363帧 / 15.06秒 / 5.2MB（实测）
* ⚠️ **禁止使用 `-c:v libx264` 等重编码选项** — 服务器 FFmpeg 编译时禁用了 h264 解码器，重编码会报错。用 `-c copy` / `-c:v copy` 即可
* ⚠️ **禁止用 `ffmpeg -i input.mp4 ...` 后直接 pipe 到 ffprobe** — 受限环境下游 `ffprobe` 会报 `Unable to create decoder` 看似损坏，实际文件完好。用 `ffprobe -v quiet -print_format json` 或仅查看文件大小判断

### 4. 下载 — proxy 绕过是关键

* CDN 域名 `platform-outputs.agnes-ai.space` 常被代理重置（curl exit code 35）
* **正确**：`curl -L --noproxy '*'` 直连下载（实测 1.2\~2.2 MB 正常）
* **错误**：带代理下载 → 连接重置 / 0字节
* `wget` 无论何种情况都返回空文件

### 5. 异步轮询模式

* 用 `terminal(background=true, notify_on_complete=true)` 启动 bash 轮询脚本
* 轮询间隔 15 秒，超时设 60 次（约 15 分钟上限）
* 轮询脚本应检查 `status == completed` + `remixed_from_video_id` 非空
* 完成后用 `MEDIA:<path>` 通过飞书直接发送

## 参考文件

* `references/api_reference.md` — 完整 API 参考（端点、参数、返回值、错误码）
* `references/2026-06-03_test_session.md` — 真实测试记录（Google Storage 超时、视频排队时间、结果字段名）
* `references/hermes-plugin-integration.md` — Hermes 插件集成指南（目录结构、save\_url\_video 坑、注册模式）
* `scripts/poll_video.py` — Python 异步视频轮询脚本
* `scripts/submit_and_poll.sh` — 一站式提交+轮询+下载脚本（用法：`bash scripts/submit_and_poll.sh "english prompt" output_name`）

## 步骤

1. **准备输入** — 确认输入数据和参数完整
2. **执行处理** — 调用工具完成核心逻辑
3. **输出结果** — 生成目标产物（文件/报告/状态）
4. **异常处理** — 失败时返回错误信息，不
