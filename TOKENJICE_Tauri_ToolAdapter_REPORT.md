# TokenJuice + Tauri + 谈判工具适配器 — 全面评估报告

> 评估日期：2026-09-17

---

## Part 1: TokenJuice 压缩集成评估

### 1.1 OpenHuman TokenJuice 技术分析

根据公开逆向信息（无开源代码，基于公开文章/演讲推断）：

| 维度 | 推测 |
|------|------|
| 算法类型 | 文本摘要 + 语义压缩混合 |
| 压缩机制 | 对长文本提取关键语义单元，丢弃冗余修辞 |
| 3.7x 容量 | 存储层面：原文 100KB → 压缩后 ~27KB（保留语义） |
| 无损 | 关键信息保留，但修辞细节可能丢失 |
| 适用场景 | 长期记忆归档（旧对话历史）、文档存储 |

### 1.2 我们当前 LoPace 对比

| 维度 | LoPace | TokenJuice（推测） |
|------|--------|-------------------|
| 压缩率 | 72% token 节省 | ~73% 存储节省（3.7x） |
| 层级 | 推理时压缩 | 存储时压缩 |
| 实现 | 开源可查 | 未开源，需自行实现 |
| 适用 | 对话历史压缩 | 归档文档压缩 |

### 1.3 集成方案

```python
# observation_pack.py 集成 TokenJuice 风格压缩

class ObservationPackWithTokenJuice:
    """ObservationPack + TokenJuice 风格压缩"""
    
    def archive_with_compression(self, content: str, content_type: str = "text") -> Dict:
        """归档时应用 TokenJuice 风格压缩"""
        # 1. 原始归档（保留）
        original_handle = self.archive(content, content_type)
        
        # 2. TokenJuice 压缩版
        compressed = self._tokenjuice_compress(content)
        compressed_handle = self.archive(compressed, content_type, metadata={
            "compressed": True,
            "compression_ratio": len(compressed) / len(content),
            "original_handle": original_handle["content_id"]
        })
        
        return {
            "original": original_handle,
            "compressed": compressed_handle,
            "savings_ratio": 1 - len(compressed) / len(content)
        }
    
    def _tokenjuice_compress(self, text: str) -> str:
        """TokenJuice 风格压缩：保留关键语义单元"""
        # Step 1: 提取关键句（去除冗余修辞）
        # Step 2: 保留实体（人名/数字/日期）
        # Step 3: 保留逻辑连接词（因果/转折/条件）
        
        sentences = text.split('。')
        key_sentences = []
        
        for sent in sentences:
            # 保留包含数字的句子（关键数据）
            if any(c.isdigit() for c in sent):
                key_sentences.append(sent)
                continue
            # 保留包含逻辑词的句子
            if any(w in sent for w in ['因为', '所以', '如果', '但是', '因此', '必须']):
                key_sentences.append(sent)
                continue
            # 保留短句（信息密度高）
            if len(sent) < 20:
                key_sentences.append(sent)
                continue
        
        return '。'.join(key_sentences)
```

### 1.4 验证计划

| 阶段 | 目标 | 时间 |
|------|------|------|
| 单元测试 | 压缩后关键信息保留率 | 2h |
| 集成测试 | 7 天工作流归档压缩比 | 1 天 |
| A/B 对比 | LoPace vs TokenJuice vs 混合方案 | 2 天 |

---

## Part 2: Tauri 桌面端方案评估

### 2.1 Tauri vs Electron vs Flutter

| 维度 | Tauri | Electron | Flutter Desktop |
|------|-------|----------|-----------------|
| 内存 | **~50-80MB** | 300-800MB | 150-300MB |
| 启动速度 | **快** | 慢 | 中 |
| 安装包 | ~5MB | ~50MB | ~30MB |
| Rust 依赖 | ✅ 需要 | ❌ 不需要 | ❌ 不需要 |
| 前端灵活性 | WebView（HTML/CSS/JS） | WebView（HTML/CSS/JS） | Dart 自绘 |
| 系统API | Rust 直接调用 | Node.js 调用 | Platform Channel |
| 学习曲线 | 中高（需 Rust） | 低（前端直接上手） | 中（需 Dart） |

### 2.2 推荐架构

```
┌──────────────────────────────────────────────────────────┐
│                  BOSS-AI-R Desktop (Tauri)                │
├──────────────────────────────────────────────────────────┤
│  前端：Vue 3 + TypeScript + Pinia                         │
│  ├── 谈判实时页（滚动字幕 + 提示气泡）                       │
│  ├── 会议列表页（时间轴 + 说话人标签）                      │
│  ├── 决策追溯页（原声回跳 + 让步轨迹）                      │
│  └── 设置页（订阅/隐私/外脑管理）                          │
├──────────────────────────────────────────────────────────┤
│  后端：Rust + tokio                                       │
│  ├── 本地推理引擎（sherpa-onnx ASR + 小模型 LLM）           │
│  ├── 云端连接（WebSocket 实时通道）                        │
│  ├── 本地存储（SQLite + 文件加密）                         │
│  └── BLE 管理（蓝牙耳机/手表连接）                         │
└──────────────────────────────────────────────────────────┘
```

### 2.3 验证计划

| 阶段 | 目标 |
|------|------|
| POC | 最小可运行 Tauri 应用 + 录音 + WebSocket 连接 |
| 内存测试 | 对比 Tauri vs Flutter 常驻内存 |
| 安装包测试 | 打包 + 安装 + 自动更新 |

---

## Part 3: 谈判工具适配器生态设计

### 3.1 适配器架构

```
┌─────────────────────────────────────────────────────────┐
│                 NegotiationAdapterManager                │
├─────────────────────────────────────────────────────────┤
│  register_adapter(name: str, adapter: ToolAdapter)       │
│  get_adapter(name: str) -> ToolAdapter                  │
│  list_adapters() -> List[str]                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ CRMAdapter  │  │EmailAdapter │  │CalendarAdapter│    │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ContractAdapter│ │PaymentAdapter│ │ReportAdapter │    │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 3.2 适配器清单

| 适配器 | 优先级 | 功能 | 对接方式 |
|--------|--------|------|---------|
| CRM | P0 | 客户信息查询/更新 | REST API |
| 邮件 | P0 | 发送会议纪要/报价 | SMTP/API |
| 日历 | P1 | 会议提醒/录音计划 | CalDAV/API |
| 合同 | P1 | 合同审查/风险标注 | OCR + LLM |
| 支付 | P2 | 定金/尾款提醒 | 支付API |
| 报表 | P2 | 谈判分析/让步轨迹 | 内部系统 |

### 3.3 统一接口

```python
class ToolAdapter:
    """统一工具适配器接口"""
    
    @abstractmethod
    async def execute(self, action: str, params: dict) -> dict:
        """执行工具操作"""
        pass
    
    @abstractmethod
    async def validate(self, action: str, params: dict) -> bool:
        """验证操作参数"""
        pass
    
    @abstractmethod
    def get_schema(self) -> dict:
        """返回工具能力描述（给 LLM 调用）"""
        pass
```

---

## Part 4: 合规沙盒隔离层设计

### 4.1 威胁模型

| 威胁 | 影响 | 等级 |
|------|------|------|
| LLM 幻觉发送邮件 | 误发含错误信息的邮件 | 🔴 高 |
| LLM 幻觉删除文件 | 重要文档被误删 | 🔴 高 |
| LLM 幻觉修改合同 | 合同条款被篡改 | 🔴 高 |
| 越权访问敏感文件 | 隐私文件被读取 | 🟡 中 |
| 未经授权的网络请求 | 数据泄露到外部 | 🟡 中 |

### 4.2 沙盒架构

```
┌─────────────────────────────────────────────────────────┐
│                    LLM Agent Layer                       │
│  (只能生成"操作意图"，不能直接执行)                        │
└──────────────────────┬──────────────────────────────────┘
                       │ operation_intent
                       ▼
┌─────────────────────────────────────────────────────────┐
│              Compliance Sandbox Layer                    │
│  ┌─────────────────────────────────────────────────┐    │
│  │  1. 意图解析（提取操作类型 + 目标 + 参数）        │    │
│  │  2. 规则匹配（白名单/黑名单/需确认列表）          │    │
│  │  3. 权限检查（文件系统/网络/外设访问控制）        │    │
│  │  4. 用户确认（高风险操作弹框确认）                │    │
│  │  5. 审计日志（全量记录，不可篡改）               │    │
│  └─────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────┘
                       │ validated_operation
                       ▼
┌─────────────────────────────────────────────────────────┐
│              Actual Execution Layer                      │
│  (真实文件操作/网络请求/外设控制)                         │
└─────────────────────────────────────────────────────────┘
```

### 4.3 规则配置

```yaml
# compliance_rules.yaml
rules:
  # 文件操作
  - action: file.read
    paths: ["~/Documents/**", "~/Downloads/**"]
    require_confirmation: false
    
  - action: file.write
    paths: ["~/Documents/BOSS-AI-R/**"]
    require_confirmation: true
    log_level: warn
    
  - action: file.delete
    paths: ["~/Documents/BOSS-AI-R/temp/**"]
    blocked_paths: ["~/Documents/**"]
    require_confirmation: true
    log_level: error
    
  # 网络操作
  - action: network.request
    allowed_domains: ["api. Boss-ai-r.com", "api.tencent.com"]
    blocked_domains: ["*.weibo.com", "*.xiaohongshu.com"]
    
  # 邮件操作
  - action: email.send
    require_confirmation: true
    max_per_hour: 10
    log_level: error
```

---

*报告生成时间：2026-09-17*
