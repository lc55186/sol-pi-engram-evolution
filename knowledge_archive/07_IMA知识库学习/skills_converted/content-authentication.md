---
name: content-authentication
description: 多模态AI内容鉴真框架
version: 1.0.0
category: security
tags: ["content-authentication", "multi-modal", "AIGC-detection", "deepfake", "creator-profiling"]
metadata:
  hermes:
    tags: ["content-authentication", "multi-modal", "AIGC-detection", "deepfake", "creator-profiling"]
    source: IMA 知识库导入
---

# content-authentication

> 多模态AI内容鉴真框架。识别合成/篡改/伪造痕迹，输出可解释判定依据与处理建议。触发词：内容鉴真 / AI内容检测 / Deepfake检测 / 伪造识别 / 真实性验证 / AIGC检测 / 创作者画像 / 反欺诈。

# Content Authentication Agent — 多模态AI内容鉴真框架

> 构建多模态AI内容鉴真Agent：识别合成/篡改/伪造痕迹，输出可解释的判定依据与处理建议。

**触发词**：内容鉴真 / AI内容检测 / Deepfake检测 / 伪造识别 / 真实性验证 / AIGC检测 / 创作者画像 / 反欺诈 / 美妆鉴真

***

## 核心能力矩阵

| **模态** | **方法数** | **代表方法**                  | **输出**           |
| ------ | ------- | ------------------------- | ---------------- |
| 文本     | 9种      | Perplexity+风格漂移+AI特征词+多尺度 | AI概率+风格偏离+异常定位   |
| 图像     | 9种      | ELA+噪声分析+边缘伪影+EXIF+社媒专用   | 篡改区域+压缩异常+平台签名   |
| 视频     | 8种      | 面部时序+帧间压缩+唇音同步+音视频联合      | Deepfake概率+跨模态异常 |
| 音频     | 6种      | 频谱异常+TTS指纹+环境声+活体+声道      | TTS概率+声纹偏离       |
| 创作者    | 7种      | 行为节律+内容指纹+互动质量+行为序列       | 机器行为概率+风险标记      |

详见 `references/detection-methods.md`

***

## 增强模块 (T7/I8/V7/C6)

基于2026-08-06 GitHub开源项目调研新增（v2.0）：

### T7 — 多尺度文本检测 (MultiscaleTextDetector)

* **来源**: AIGC\_text\_detector (⭐453, ICLR'24)
* **核心**: 句子级+段落级+文档级三层AI特征融合
* **特点**: 比整文档检测准确度高30%+

### I8 — 社交媒体图像检测 (SocialMediaImageDetector)

* **来源**: SIDA (⭐162)
* **核心**: 平台压缩签名匹配+美颜/滤镜检测+二次截图检测+AI生图痕迹
* **特点**: 针对小红书/抖音/微博等中文平台优化

### V7 — 音视频联合检测 (AudioVideoFusionDetector)

* **来源**: OpenAVFF
* **核心**: 唇音同步+跨模态语义一致性+音频活体检测
* **特点**: 解决跨模态伪造（AI视频+真人音频）

### C6 — 行为序列分析 (BehaviorSequenceAnalyzer)

* **核心**: 发布间隔规律性+互动爆发检测+发布量异常检测
* **特点**: 从时间序列角度识别机器账号

***

## 标准工作流程

### 1. 内容接入

```python
content = {
    "id": "content_id",
    "text": "文案内容",
    "images": ["path/to/image.jpg", ...],
    "video": "path/to/video.mp4",
    "audio": "path/to/audio.wav",
    "creator_id": "creator_xxx",
    "creator_history": ["历史作品1", ...],
    "creator_posts": [
        {"timestamp": ..., "content": "...", "engagement": {"likes": 100, "comments": 10}}
    ]
}
```

### 2. 多模态并行检测

* 各模态检测器独立运行，互不阻塞
* 每个检测器返回 Evidence 对象：(模态, 方法, 分数0-1, 描述, 详情)
* 同模态多条证据取最高分作为该模态分数

### 3. 创作者画像查询

* 根据creator\_id查询历史画像
* 计算新内容与历史基线的偏离度
* 偏离度作为独立证据加入决策

### 4. 风险融合决策

* 各模态分数按权重加权求和
* 跨模态交叉验证：≥2模态同时异常 → 置信度+8%；≥3模态 → +15%
* 阈值判定：
  * `score >= 0.7` → FORGED（伪造）
  * `score >= 0.4` → SUSPICIOUS（可疑）
  * `score < 0.4` → GENUINE（真实）

### 5. 报告生成

* Markdown：证据链+热力条+处理建议
* HTML：可视化热力图+样式化输出
* JSON：结构化数据，便于API调用

***

## 决策引擎权重配置

```python
MODALITY_WEIGHTS = {
    "text": 0.25,
    "image": 0.30,
    "video": 0.25,
    "audio": 0.10,
    "creator": 0.10
}
```

***

## 关键设计原则

1. **可解释优先**：每个判定必须附带证据链，不做黑盒
2. **人在回路**：高置信自动处理，中低置信人工复核
3. **对抗演进**：定期用最新生成模型测试检测器，持续更新
4. **跨模态增强**：多模态同时异常时提升置信度
5. **创作者维度**：从内容扩展到账号行为，发现代刷/买号

***

## Pitfalls

* **单模态误报**：ELA/EXIF异常不一定代表伪造，需结合其他模态验证
* **风格漂移阈值**：创作者换风格是正常的，需区分"突变"和"演进"
* **数据冷启动**：新创作者无历史画像时，纯依赖内容检测，置信度下调
* **对抗样本**：恶意用户可能模拟真实风格绕过检测，需持续更新特征库

***

## 参考实现

* **项目位置**：`/root/workspace/projects/beauty-ai-authenticator/`
* `src/detection_engine_v2.py` — 1463行，**39种方法**，5大模态
* `src/report_generator.py` — 报告生成器（MD/HTML/JSON三格式）
* `beauty_authenticator_cli.py` — **独立CLI入口**，可直接运行
* `config.json` — 配置文件，支持自定义权重/阈值/模块开关
* `tests/test_suite.py` — 原始测试套件（21用例）
* `tests/test_suite_v2.py` — **综合测试套件（37用例，100%通过）**
* `docs/comprehensive-report.md` — 综合评估报告

快速验证：

```bash
cd /root/workspace/projects/beauty-ai-authenticator

# 核心引擎Demo
python3 src/detection_engine_v2.py

# 综合测试（37用例）
python3 tests/test_suite_v2.py

# CLI入口（独立运行）
python3 beauty_authenticator_cli.py --text "文案内容" --output report.md
python3 beauty_authenticator_cli.py --image product.jpg --platform xiaohongshu
python3 beauty_authenticator_cli.py --video review.mp4
python3 beauty_authenticator_cli.py --full content.json
python3 beauty_authenticator_cli.py --batch contents.json
```

**关键发现（2026-08-06调研）**：

1. **社交媒体专用检测是蓝海**：通用检测器未针对平台压缩/滤镜优化
2. **多尺度是趋势**：AIGC\_text\_detector的多尺度token级检测效果远超整文档
3. **音视频联合是短板**：大多数项目只做单模态，跨模态联合是前沿
4. **Agent封装是刚需**：detect-skill证明市场需要完整Agent方案

***

## References

* `references/detection-methods.md` — 39种检测方法的原理与评估
* `references/implementation-notes.md` — 关键实现细节与优化策略
* `references/v2.0-enhancements.md` — **v2.0增强模块详细笔记** (T7/I8/V7/C6)
* `references/github-research-20260806.md` — 2026-08-06 GitHub开源项目调研笔记
* `scripts/quick_verify.py` — **快速验证脚本**（独立运行CLI验证）


