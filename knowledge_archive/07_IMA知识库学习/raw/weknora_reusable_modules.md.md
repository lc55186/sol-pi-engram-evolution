# WeKnora — 可复用模块深度拆解

> **仓库**: https://github.com/Tencent/WeKnora
> **分析日期**: 2026-09-18
> **描述**: 深度拆解 WeKnora 源码，提取可直接复用的模块

---

## 模块概览

| 模块 ID | 名称 | 语言 | 描述 |
|---------|------|------|------|
| mcpserver | MCP Server 实现 | Go | 基于 mcp-go 的 MCP (Model Context Protocol) 服务器，提供 Streamable HTTP 传输，支持工具注册、权限控制、速率限制 |
| agent_tools_registry | Agent 工具编排系统 | Go | 可扩展的工具注册框架，支持工具注册、参数校验、输出截断、能力过滤 |
| docreader_parser | 文档解析引擎 | Python | 多格式文档解析器，支持 20+ 文件格式，可提取文本和图片引用 |
| knowledge_types | 知识库类型定义 | Go | 知识库、文档、分块等核心领域模型和业务逻辑 |

---

## MCP Server 实现 `mcpserver`

- **路径**: `internal/mcpserver/`
- **语言**: Go
- **描述**: 基于 mcp-go 的 MCP (Model Context Protocol) 服务器，提供 Streamable HTTP 传输，支持工具注册、权限控制、速率限制

### 关键文件

- `server.go`
- `tools_retrieve.go`
- `tools_ask.go`
- `tools_ingest.go`
- `tools_wiki.go`
- `scope.go`

### 接口定义

#### Server (struct)

MCP 服务器核心结构体

| 方法 | 签名 | 描述 |
|------|------|------|
| NewServer | `func NewServer(kbService, knowledgeService, chunkService, wikiService, sessionService, messageService, agentService, kbShareService, tenantService, endpointRepo, db, cfg, redisClient) *Server` | 构建 MCP 服务器实例，初始化工具目录和 Streamable HTTP 传输 |
| Handler | `func (s *Server) Handler() http.Handler` | 返回 http.Handler，挂载到 /mcp/:endpoint_id 路由 |
| filterTools | `func (s *Server) filterTools(ctx context.Context, all []mcp.Tool) []mcp.Tool` | 根据端点权限过滤可见工具 |
| guardTool | `func (s *Server) guardTool(next server.ToolHandlerFunc) server.ToolHandlerFunc` | 工具调用中间件，执行权限校验和速率限制 |

### 工具目录

| 工具名 | 描述 |
|--------|------|
| list_knowledge_bases | 列出可访问的知识库 |
| search_knowledge | 语义/关键词/混合检索知识库 |
| grep_chunks | 正则表达式搜索文本块 |
| list_documents | 列出知识库中的文档 |
| read_document | 读取文档内容和分块 |
| ask | 综合回答并引用来源 |
| wiki_search | 搜索 Wiki 页面 |
| wiki_read_page | 读取 Wiki 页面 |
| wiki_index | 获取 Wiki 索引 |
| add_document | 添加文档 |
| update_document | 更新文档 |
| delete_document | 删除文档 |

### 依赖

`github.com/mark3labs/mcp-go`, `github.com/redis/go-redis/v9`, `gorm.io/gorm`

### 复用指引

1. 实现 interfaces.KnowledgeBaseService 等接口
2. 调用 NewServer() 传入依赖
3. 将 Handler() 挂载到 HTTP 路由
4. 通过 MCPEndpointAuth 中间件认证

---

## Agent 工具编排系统 `agent_tools_registry`

- **路径**: `internal/agent/tools/`
- **语言**: Go
- **描述**: 可扩展的工具注册框架，支持工具注册、参数校验、输出截断、能力过滤

### 关键文件

- `registry.go`
- `search_knowledge.go`
- `read_document.go`
- `list_documents.go`
- `capabilities.go`

### 接口定义

#### ToolRegistry (struct)

工具注册表，管理工具的注册和执行

| 方法 | 签名 | 描述 |
|------|------|------|
| RegisterTool | `func (r *ToolRegistry) RegisterTool(tool types.Tool)` | 注册工具（首次注册优先，防止名称劫持） |
| RegisterDeferredTool | `func (r *ToolRegistry) RegisterDeferredTool(tool types.Tool)` | 注册延迟工具（不暴露给模型） |
| ExecuteTool | `func (r *ToolRegistry) ExecuteTool(ctx context.Context, name string, args json.RawMessage) (*types.ToolResult, error)` | 执行指定工具 |
| GetFunctionDefinitions | `func (r *ToolRegistry) GetFunctionDefinitions() []types.FunctionDefinition` | 获取所有工具的功能定义（用于 LLM） |

#### SearchKnowledgeTool (struct)

知识库搜索工具，支持 hybrid/semantic/keyword 模式

**关键特性**:
- 并发多目标搜索
- Rerank 重排序
- MMR 去冗余
- 模式降级（vector-only/keyword-only KB 自动适配）
- 图片信息懒加载

#### ReadDocumentTool (struct)

文档读取工具，支持分页、按块读取、正则搜索

#### ListDocumentsTool (struct)

文档列表工具，支持 @file/@tag 范围过滤

### 依赖

`encoding/json`, `github.com/Tencent/WeKnora/internal/types`, `github.com/Tencent/WeKnora/internal/models/rerank`

### 复用指引

1. 实现 types.Tool 接口创建自定义工具
2. 使用 NewToolRegistry() 创建注册表
3. 调用 RegisterTool() 注册工具
4. 调用 ExecuteTool() 执行工具调用
5. 使用 GetFunctionDefinitions() 获取 LLM 可用的工具描述

---

## 文档解析引擎 `docreader_parser`

- **路径**: `docreader/`
- **语言**: Python
- **描述**: 多格式文档解析器，支持 20+ 文件格式，可提取文本和图片引用

### 关键文件

- `parser/base_parser.py`
- `parser/parser.py`
- `parser/registry.py`
- `parser/pdf_parser.py`
- `parser/docx_parser.py`
- `parser/excel_parser.py`
- `parser/html_parser.py`
- `parser/markdown_parser.py`
- `splitter/splitter.py`
- `splitter/header_hook.py`
- `models/document.py`
- `client/client.go`

### 接口定义

#### BaseParser (abstract_class)

解析器基类，定义 parse_into_text 接口

| 方法 | 签名 | 描述 |
|------|------|------|
| parse_into_text | `def parse_into_text(self, content: bytes) -> Document` | 将文档内容解析为 Markdown 文本 |
| parse | `def parse(self, content: bytes) -> Document` | 解析文档并返回 Markdown + 图片引用 |

#### ParserEngineRegistry (class)

解析引擎注册表，管理多种解析引擎和文件类型的映射

| 方法 | 签名 | 描述 |
|------|------|------|
| register | `def register(self, name, file_types, description, check_available, unavailable_hint)` | 注册解析引擎 |
| get_parser_class | `def get_parser_class(self, engine: str, file_type: str) -> Type[BaseParser]` | 根据引擎和文件类型获取解析器类 |
| list_engines | `def list_engines(self, overrides) -> List[Dict]` | 列出所有可用引擎 |

#### TextSplitter (class)

文本分块器，支持保护正则、表头追踪、智能合并

| 方法 | 签名 | 描述 |
|------|------|------|
| split_text | `def split_text(self, text: str) -> List[Tuple[int, int, str]]` | 将文本分割为重叠的块 |
| restore_text | `def restore_text(self, chunks) -> str` | 从块恢复原始文本（去除重叠） |

#### HeaderTracker (class)

表头追踪 Hook，在分块时保持表格上下文

#### Document (PydanticModel)

undefined

| 字段 | 类型 |
|------|------|
| content | str |
| images | Dict[str, str] |
| chunks | List[Chunk] |
| metadata | Dict[str, Any] |

### 支持格式

`PDF`, `DOCX`, `DOC`, `XLSX`, `XLS`, `PPTX`, `PPT`, `EPUB`, `HTML`, `HTM`, `MHTML`, `Markdown`, `XMind`, `JPG`, `JPEG`, `PNG`, `GIF`, `BMP`, `TIFF`, `WebP`, `CSV`

### 解析引擎

- **builtin**: 内置解析引擎 (docx, doc, pdf, md, xlsx, xls, pptx, ppt, epub, html, mhtml, xmind, images)
- **markitdown**: 微软 MarkItDown 库 (md, pdf, docx, doc, pptx, ppt, xlsx, xls, csv)
- **opendataloader**: OpenDataLoader PDF 引擎（需 Java 11+） (pdf)

### 依赖

`pydantic`, `python-docx`, `openpyxl`, `pypdf`, `pdfplumber`, `markitdown`, `beautifulsoup4`, `lxml`, `paddleocr`, `paddleocr-vl`, `grpcio`, `grpcio-tools`

### 复用指引

1. 创建 ParserEngineRegistry 实例
2. 调用 get_parser_class(engine, file_type) 获取解析器
3. 调用 parser.parse(content) 获取 Document
4. 使用 TextSplitter 进行文本分块
5. 通过 gRPC 客户端调用远程 DocReader 服务

---

## 知识库类型定义 `knowledge_types`

- **路径**: `internal/types/`
- **语言**: Go
- **描述**: 知识库、文档、分块等核心领域模型和业务逻辑

### 关键文件

- `knowledge.go`

### 接口定义

#### Knowledge (struct)

知识文档实体，包含元数据和解析状态

| 字段 | 类型 |
|------|------|
| 0 | ID |
| 1 | TenantID |
| 2 | KnowledgeBaseID |
| 3 | Type |
| 4 | Title |
| 5 | Description |
| 6 | Source |
| 7 | Channel |
| 8 | ParseStatus |
| 9 | FileName |
| 10 | FileType |
| 11 | FileSize |
| 12 | Content |
| 13 | Metadata |
| 14 | CreatedAt |
| 15 | UpdatedAt |

#### KnowledgeBase (struct)

知识库实体

#### SearchTarget (struct)

搜索目标，支持跨租户搜索

| 字段 | 类型 |
|------|------|
| 0 | Type |
| 1 | KnowledgeBaseID |
| 2 | TenantID |
| 3 | KnowledgeIDs |
| 4 | TagIDs |

### 依赖

`gorm.io/gorm`, `github.com/google/uuid`

### 复用指引

1. 导入 types 包
2. 使用 Knowledge 结构体进行 CRUD
3. 使用 KnowledgeListFilter 构建查询过滤条件
4. 使用 SearchTargets 指定搜索范围

---

## 集成模式

### MCP Server 集成 Agent Tools

MCP Server 通过调用 Agent Tools 实现工具执行

```
MCP Client -> Server.Handler() -> guardTool() -> agentTool.Execute() -> toolResultFromAgentTool() -> MCP Response
```

### Agent Tools 依赖 Knowledge Service

Agent 工具通过接口调用知识库服务

```
AgentTool.Execute() -> interfaces.KnowledgeService/ChunkService/KnowledgeBaseService -> Repository -> Database
```

### DocReader gRPC 服务

文档解析通过 gRPC 服务独立部署

```
Go App -> docreader.Client -> gRPC -> DocReader Python Service -> Parser -> Document
```

---

## 关键设计模式

### Interface-Driven Design

所有依赖通过接口注入，便于测试和替换实现

- `interfaces.KnowledgeBaseService`
- `interfaces.ChunkService`
- `interfaces.DocumentReader`
- `rerank.Reranker`

### Tool Capability Filtering

根据知识库能力（vector/keyword/wiki/graph/faq）自动过滤可用工具

> 文件: `internal/agent/tools/capabilities.go`

### Deferred Tool Registration

延迟注册工具，先保留执行能力，完成注册后才暴露给模型

> 文件: `internal/agent/tools/registry.go`

### Parser Engine Registry

解析引擎注册表模式，支持运行时切换和降级

> 文件: `docreader/parser/registry.py`

### Streaming gRPC

大文件使用 server-streaming RPC 避免消息大小限制

> 文件: `docreader/proto/docreader.proto`

---

## 复用推荐场景

| 场景 | 模块 | 描述 |
|------|------|------|
| 构建 RAG 系统 | docreader_parser, knowledge_types, agent_tools_registry | 使用文档解析引擎提取文本，通过知识库类型管理文档，用工具编排实现检索 |
| 构建 MCP 服务 | mcpserver | 基于 mcp-go 快速搭建 MCP 服务器，支持 Streamable HTTP 传输 |
| 构建 AI Agent | agent_tools_registry, knowledge_types | 使用工具注册框架管理 Agent 工具，通过知识库接口获取上下文 |
| 多格式文档解析 | docreader_parser | 独立使用文档解析模块，支持 20+ 文件格式和多种解析引擎 |

