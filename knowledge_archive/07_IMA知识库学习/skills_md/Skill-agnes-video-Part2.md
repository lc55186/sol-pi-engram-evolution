# Skill-agnes-video-Part2

wget 0字节）

curl -L -o /tmp/video.mp4 "[https://platform-outputs.agnes-ai.space/videos/](https://platform-outputs.agnes-ai.space/videos/)..."

wget -q -O /tmp/video.mp4 "[https://platform-outputs.agnes-ai.space/videos/](https://platform-outputs.agnes-ai.space/videos/)..."

````

### 3. 免费版时长限制 & 速率限制
- 免费版单次最多 10 秒（241帧@24fps），实际常见 3-5 秒
- `seconds` 字段在提交时就确定，不是 max 而是实际分配
- **速率限制**：1 request/minute，连续提交会报 `rate_limit_exceeded`
- **分段制作策略**：需要 >10s 视频时，拆为数段（每段 ~5s / 121帧），间隔 60-90s 提交，然后 `ffmpeg -f concat -c copy` 拼接
 ```bash
 # 例：三段拼接为 15s 竖版
 echo "file '/tmp/part1.mp4'" > /tmp/concat.txt
 echo "file '/tmp/part2.mp4'" >> /tmp/concat.txt
 echo "file '/tmp/part3.mp4'" >> /tmp/concat.txt
 ffmpeg -y -f concat -safe 0 -i /tmp/concat.txt -c copy /tmp/final.mp4
````

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
4. **异常处理** — 失败时返回错误信息，不静默

## 验证

- [ ] 输出文件/报告已生成

- [ ] 处理逻辑覆盖主要场景

- [ ] 错误情况有明确提示

- [ ] 输出格式符合预期
