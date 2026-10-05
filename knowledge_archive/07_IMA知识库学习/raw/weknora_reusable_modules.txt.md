{
  "analysis_metadata": {
    "project": "WeKnora",
    "repository": "https://github.com/Tencent/WeKnora",
    "analysis_date": "2026-09-18",
    "description": "深度拆解 WeKnora 源码，提取可直接复用的模块"
  },
  "reusable_modules": [
    {
      "id": "mcpserver",
      "name": "MCP Server 实现",
      "path": "internal/mcpserver/",
      "language": "Go",
      "description": "基于 mcp-go 的 MCP (Model Context Protocol) 服务器，提供 Streamable HTTP 传输，支持工具注册、权限控制、速率限制",
      "key_files": [
        "server.go",
        "tools_retrieve.go",
        "tools_ask.go",
        "tools_ingest.go",
        "tools_wiki.go",
        "scope.go"
      ],
      "interfaces": [
        {
          "name": "Server",
          "type": "struct",
          "description": "MCP 服务器核心结构体",
          "methods": [
            {
              "name": "NewServer",
              "signature": "func NewServer(kbService, knowledgeService, chunkService, wikiService, sessionService, messageService, agentService, kbShareService, tenantService, endpointRepo, db, cfg, redisClient) *Server",
              "description": "构建 MCP 服务器实例，初始化工具目录和 Streamable HTTP 传输"
            },
            {
              "name": "Handler",
              "signature": "func (s *Server) Handler() http.Handler",
              "description": "返回 http.Handler，挂载到 /mcp/:endpoint_id 路由"
            },
            {
              "name": "filterTools",
              "signature": "func (s *Server) filterTools(ctx context.Context, all []mcp.Tool) []mcp.Tool",
              "description": "根据端点权限过滤可见工具"
            },
            {
              "name": "guardTool",
              "signature": "func (s *Server) guardTool(next server.ToolHandlerFunc) server.ToolHandlerFunc",
              "description": "工具调用中间件，执行权限校验和速率限制"
            }
          ]
        }
      ],
      "tool_catalog": [
        {"name": "list_knowledge_bases", "description": "列出可访问的知识库"},
        {"name": "search_knowledge", "description": "语义/关键词/混合检索知识库"},
        {"name": "grep_chunks", "description": "正则表达式搜索文本块"},
        {"name": "list_documents", "description": "列出知识库中的文档"},
        {"name": "read_document", "description": "读取文档内容和分块"},
        {"name": "ask", "description": "综合回答并引用来源"},
        {"name": "wiki_search", "description": "搜索 Wiki 页面"},
        {"name": "wiki_read_page", "description": "读取 Wiki 页面"},
        {"name": "wiki_index", "description": "获取 Wiki 索引"},
        {"name": "add_document", "description": "添加文档"},
        {"name": "update_document", "description": "更新文档"},
        {"name": "delete_document", "description": "删除文档"}
      ],
      "dependencies": [
        "github.com/mark3labs/mcp-go",
        "github.com/redis/go-redis/v9",
        "gorm.io/gorm"
      ],
      "reuse_instructions": "1. 实现 interfaces.KnowledgeBaseService 等接口\n2. 调用 NewServer() 传入依赖\n3. 将 Handler() 挂载到 HTTP 路由\n4. 通过 MCPEndpointAuth 中间件认证"
    },
    {
      "id": "agent_tools_registry",
      "name": "Agent 工具编排系统",
      "path": "internal/agent/tools/",
      "language": "Go",
      "description": "可扩展的工具注册框架，支持工具注册、参数校验、输出截断、能力过滤",
      "key_files": [
        "registry.go",
        "search_knowledge.go",
        "read_document.go",
        "list_documents.go",
        "capabilities.go"
      ],
      "interfaces": [
        {
          "name": "ToolRegistry",
          "type": "struct",
          "description": "工具注册表，管理工具的注册和执行",
          "methods": [
            {
              "name": "RegisterTool",
              "signature": "func (r *ToolRegistry) RegisterTool(tool types.Tool)",
              "description": "注册工具（首次注册优先，防止名称劫持）"
            },
            {
              "name": "RegisterDeferredTool",
              "signature": "func (r *ToolRegistry) RegisterDeferredTool(tool types.Tool)",
              "description": "注册延迟工具（不暴露给模型）"
            },
            {
              "name": "ExecuteTool",
              "signature": "func (r *ToolRegistry) ExecuteTool(ctx context.Context, name string, args json.RawMessage) (*types.ToolResult, error)",
              "description": "执行指定工具"
            },
            {
              "name": "GetFunctionDefinitions",
              "signature": "func (r *ToolRegistry) GetFunctionDefinitions() []types.FunctionDefinition",
              "description": "获取所有工具的功能定义（用于 LLM）"
            }
          ]
        },
        {
          "name": "SearchKnowledgeTool",
          "type": "struct",
          "description": "知识库搜索工具，支持 hybrid/semantic/keyword 模式",
          "key_features": [
            "并发多目标搜索",
            "Rerank 重排序",
            "MMR 去冗余",
            "模式降级（vector-only/keyword-only KB 自动适配）",
            "图片信息懒加载"
          ]
        },
        {
          "name": "ReadDocumentTool",
          "type": "struct",
          "description": "文档读取工具，支持分页、按块读取、正则搜索"
        },
        {
          "name": "ListDocumentsTool",
          "type": "struct",
          "description": "文档列表工具，支持 @file/@tag 范围过滤"
        }
      ],
      "types_interfaces": [
        {
          "name": "Tool",
          "definition": "interface { Name() string; Description() string; Parameters() json.RawMessage; Execute(ctx, args) (*ToolResult, error) }"
        },
        {
          "name": "ToolResult",
          "fields": {"Success": "bool", "Output": "string", "Error": "string", "Data": "map[string]interface{}"}
        },
        {
          "name": "FunctionDefinition",
          "fields": {"Name": "string", "Description": "string", "Parameters": "json.RawMessage"}
        }
      ],
      "dependencies": [
        "encoding/json",
        "github.com/Tencent/WeKnora/internal/types",
        "github.com/Tencent/WeKnora/internal/models/rerank"
      ],
      "reuse_instructions": "1. 实现 types.Tool 接口创建自定义工具\n2. 使用 NewToolRegistry() 创建注册表\n3. 调用 RegisterTool() 注册工具\n4. 调用 ExecuteTool() 执行工具调用\n5. 使用 GetFunctionDefinitions() 获取 LLM 可用的工具描述"
    },
    {
      "id": "docreader_parser",
      "name": "文档解析引擎",
      "path": "docreader/",
      "language": "Python",
      "description": "多格式文档解析器，支持 20+ 文件格式，可提取文本和图片引用",
      "key_files": [
        "parser/base_parser.py",
        "parser/parser.py",
        "parser/registry.py",
        "parser/pdf_parser.py",
        "parser/docx_parser.py",
        "parser/excel_parser.py",
        "parser/html_parser.py",
        "parser/markdown_parser.py",
        "splitter/splitter.py",
        "splitter/header_hook.py",
        "models/document.py",
        "client/client.go"
      ],
      "interfaces": [
        {
          "name": "BaseParser",
          "type": "abstract_class",
          "description": "解析器基类，定义 parse_into_text 接口",
          "methods": [
            {
              "name": "parse_into_text",
              "signature": "def parse_into_text(self, content: bytes) -> Document",
              "description": "将文档内容解析为 Markdown 文本",
              "abstract": true
            },
            {
              "name": "parse",
              "signature": "def parse(self, content: bytes) -> Document",
              "description": "解析文档并返回 Markdown + 图片引用"
            }
          ]
        },
        {
          "name": "ParserEngineRegistry",
          "type": "class",
          "description": "解析引擎注册表，管理多种解析引擎和文件类型的映射",
          "methods": [
            {
              "name": "register",
              "signature": "def register(self, name, file_types, description, check_available, unavailable_hint)",
              "description": "注册解析引擎"
            },
            {
              "name": "get_parser_class",
              "signature": "def get_parser_class(self, engine: str, file_type: str) -> Type[BaseParser]",
              "description": "根据引擎和文件类型获取解析器类"
            },
            {
              "name": "list_engines",
              "signature": "def list_engines(self, overrides) -> List[Dict]",
              "description": "列出所有可用引擎"
            }
          ]
        },
        {
          "name": "TextSplitter",
          "type": "class",
          "description": "文本分块器，支持保护正则、表头追踪、智能合并",
          "config": {
            "chunk_size": 512,
            "chunk_overlap": 80,
            "separators": ["\\n", "。", " "],
            "protected_regex": ["$$...$$", "![...](...)", "[...](...)", "```..."]
          },
          "methods": [
            {
              "name": "split_text",
              "signature": "def split_text(self, text: str) -> List[Tuple[int, int, str]]",
              "description": "将文本分割为重叠的块"
            },
            {
              "name": "restore_text",
              "signature": "def restore_text(self, chunks) -> str",
              "description": "从块恢复原始文本（去除重叠）"
            }
          ]
        },
        {
          "name": "HeaderTracker",
          "type": "class",
          "description": "表头追踪 Hook，在分块时保持表格上下文"
        },
        {
          "name": "Document",
          "type": "PydanticModel",
          "fields": {"content": "str", "images": "Dict[str, str]", "chunks": "List[Chunk]", "metadata": "Dict[str, Any]"}
        }
      ],
      "supported_formats": [
        "PDF", "DOCX", "DOC", "XLSX", "XLS", "PPTX", "PPT",
        "EPUB", "HTML", "HTM", "MHTML", "Markdown", "XMind",
        "JPG", "JPEG", "PNG", "GIF", "BMP", "TIFF", "WebP", "CSV"
      ],
      "parser_engines": [
        {"name": "builtin", "description": "内置解析引擎", "formats": ["docx", "doc", "pdf", "md", "xlsx", "xls", "pptx", "ppt", "epub", "html", "mhtml", "xmind", "images"]},
        {"name": "markitdown", "description": "微软 MarkItDown 库", "formats": ["md", "pdf", "docx", "doc", "pptx", "ppt", "xlsx", "xls", "csv"]},
        {"name": "opendataloader", "description": "OpenDataLoader PDF 引擎（需 Java 11+）", "formats": ["pdf"]}
      ],
      "dependencies": [
        "pydantic",
        "python-docx", "openpyxl", "pypdf", "pdfplumber",
        "markitdown", "beautifulsoup4", "lxml",
        "paddleocr", "paddleocr-vl",
        "grpcio", "grpcio-tools"
      ],
      "reuse_instructions": "1. 创建 ParserEngineRegistry 实例\n2. 调用 get_parser_class(engine, file_type) 获取解析器\n3. 调用 parser.parse(content) 获取 Document\n4. 使用 TextSplitter 进行文本分块\n5. 通过 gRPC 客户端调用远程 DocReader 服务"
    },
    {
      "id": "knowledge_types",
      "name": "知识库类型定义",
      "path": "internal/types/",
      "language": "Go",
      "description": "知识库、文档、分块等核心领域模型和业务逻辑",
      "key_files": [
        "knowledge.go"
      ],
      "interfaces": [
        {
          "name": "Knowledge",
          "type": "struct",
          "description": "知识文档实体，包含元数据和解析状态",
          "fields": [
            "ID", "TenantID", "KnowledgeBaseID", "Type", "Title",
            "Description", "Source", "Channel", "ParseStatus",
            "FileName", "FileType", "FileSize", "Content",
            "Metadata", "CreatedAt", "UpdatedAt"
          ],
          "constants": {
            "types": ["manual", "faq", "file", "url", "passage"],
            "parse_statuses": ["pending", "processing", "finalizing", "completed", "failed", "deleting", "cancelled"],
            "channels": ["web", "api", "wechat", "feishu", "notion", "rss", "ima"]
          }
        },
        {
          "name": "KnowledgeBase",
          "type": "struct",
          "description": "知识库实体",
          "capabilities": ["vector", "keyword", "wiki", "graph", "faq"]
        },
        {
          "name": "SearchTarget",
          "type": "struct",
          "description": "搜索目标，支持跨租户搜索",
          "fields": ["Type", "KnowledgeBaseID", "TenantID", "KnowledgeIDs", "TagIDs"]
        }
      ],
      "dependencies": [
        "gorm.io/gorm",
        "github.com/google/uuid"
      ],
      "reuse_instructions": "1. 导入 types 包\n2. 使用 Knowledge 结构体进行 CRUD\n3. 使用 KnowledgeListFilter 构建查询过滤条件\n4. 使用 SearchTargets 指定搜索范围"
    }
  ],
  "integration_patterns": [
    {
      "name": "MCP Server 集成 Agent Tools",
      "description": "MCP Server 通过调用 Agent Tools 实现工具执行",
      "flow": "MCP Client -> Server.Handler() -> guardTool() -> agentTool.Execute() -> toolResultFromAgentTool() -> MCP Response"
    },
    {
      "name": "Agent Tools 依赖 Knowledge Service",
      "description": "Agent 工具通过接口调用知识库服务",
      "flow": "AgentTool.Execute() -> interfaces.KnowledgeService/ChunkService/KnowledgeBaseService -> Repository -> Database"
    },
    {
      "name": "DocReader gRPC 服务",
      "description": "文档解析通过 gRPC 服务独立部署",
      "flow": "Go App -> docreader.Client -> gRPC -> DocReader Python Service -> Parser -> Document"
    }
  ],
  "key_design_patterns": [
    {
      "name": "Interface-Driven Design",
      "description": "所有依赖通过接口注入，便于测试和替换实现",
      "examples": [
        "interfaces.KnowledgeBaseService",
        "interfaces.ChunkService",
        "interfaces.DocumentReader",
        "rerank.Reranker"
      ]
    },
    {
      "name": "Tool Capability Filtering",
      "description": "根据知识库能力（vector/keyword/wiki/graph/faq）自动过滤可用工具",
      "file": "internal/agent/tools/capabilities.go"
    },
    {
      "name": "Deferred Tool Registration",
      "description": "延迟注册工具，先保留执行能力，完成注册后才暴露给模型",
      "file": "internal/agent/tools/registry.go"
    },
    {
      "name": "Parser Engine Registry",
      "description": "解析引擎注册表模式，支持运行时切换和降级",
      "file": "docreader/parser/registry.py"
    },
    {
      "name": "Streaming gRPC",
      "description": "大文件使用 server-streaming RPC 避免消息大小限制",
      "file": "docreader/proto/docreader.proto"
    }
  ],
  "reuse_recommendations": [
    {
      "scenario": "构建 RAG 系统",
      "modules": ["docreader_parser", "knowledge_types", "agent_tools_registry"],
      "description": "使用文档解析引擎提取文本，通过知识库类型管理文档，用工具编排实现检索"
    },
    {
      "scenario": "构建 MCP 服务",
      "modules": ["mcpserver"],
      "description": "基于 mcp-go 快速搭建 MCP 服务器，支持 Streamable HTTP 传输"
    },
    {
      "scenario": "构建 AI Agent",
      "modules": ["agent_tools_registry", "knowledge_types"],
      "description": "使用工具注册框架管理 Agent 工具，通过知识库接口获取上下文"
    },
    {
      "scenario": "多格式文档解析",
      "modules": ["docreader_parser"],
      "description": "独立使用文档解析模块，支持 20+ 文件格式和多种解析引擎"
    }
  ]
}
