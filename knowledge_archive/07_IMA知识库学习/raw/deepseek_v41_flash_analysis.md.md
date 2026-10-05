# DeepSeek V4.1 Flash — 全量技术解析与 BOSS-AI-R 影响评估

> 来源：DeepSeek官方API文档（2026-09-10/14）、HuggingFace
> 采集时间：2026-09-18（Round 20）

## 模型架构革命

### Causal-Encoder-Decoder 非对称结构
- **输入激活仅8B参数**，输出激活16B参数
- 总参数552B的MoE模型，但推理成本远低于同尺寸模型
- 这种非对称设计使得输入处理极快，输出质量极高

### KV Cache 突破
- KV Cache 压缩至上一代的 **1/4**（HBM需求）
- SSD需求减少至 **1/8**
- 从初代模型累计：KV Cache 已缩小 **437倍**
- **对BOSS-AI-R的意义**：多轮谈判场景（高上下文长度）的推理成本骤降

## 性能表现
- 在Agentic Benchmark上全面超越 DeepSeek V4 Pro
- 原生多模态视觉理解能力
- 更大规模强化学习后训练

## API变更（关键！）
- 模型名 `deepseek-flash` → 调用V4.1 Flash
- 旧版V4 Flash和V4 Flash Vision Exp已下线
- **9月14日12:00后**，`deepseek-v4-pro` 请求全部路由到V4.1 Flash，按V4.1 Flash单价计费
- V4 Pro 计划有序下线

## 定价（峰谷定价）
| 时段 | Input | Output |
|------|-------|--------|
| 高峰 | $0.15/M tokens | $0.60/M tokens |
| 闲时 | $0.075/M tokens | $0.30/M tokens |

- V4 Pro原价 $0.40/M input → 路由后实际按V4.1 Flash $0.15/M计费（**降价62.5%**）

## WorkBuddy官方合作确认
- **"腾讯（WorkBuddy、CodeBuddy）和 OpenCode 作为官方合作伙伴，现已全量接入 DeepSeek V4.1 Flash"**
- 这意味着 NBBOSS 底层模型可能已升级到 V4.1 Flash

## 开源
- HuggingFace: https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash
- 技术报告: https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/blob/main/DeepSeek_V41_Tech_Report.pdf

## 对 BOSS-AI-R 的影响（极其重要）

1. **云端推理成本降至 $0.15/M input**，BOSS-AI-R 云端方案可直接复用
2. **V4 Pro 路由到 Flash** = DeepSeek官方确认Flash已全面超越Pro，BOSS-AI-R无需等待更强模型
3. **WorkBuddy全量接入** = NBBOSS可能已升级，竞品AI能力大幅提升
4. **KV Cache压缩437倍** = Agent场景成本骤降，BOSS-AI-R的多轮谈判场景成本可控
5. **建议立即将BOSS-AI-R云端模型切换至 deepseek-flash**（已在config.py中配置完成）

## 多轮谈判场景成本估算（基于V4.1 Flash）

假设单次谈判30轮对话，每轮平均2000 input tokens + 500 output tokens：
- Input: 30 × 2000 = 60K tokens × $0.15/M = $0.009
- Output: 30 × 500 = 15K tokens × $0.60/M = $0.009
- **单次谈判成本 ≈ $0.018（约¥0.13）**
- 100次/天 × 30天 = 3000次/月 ≈ $54/月（约¥390）
- **完全可控！**

---
*Round 20 Bridge Intel | 2026-09-18*
