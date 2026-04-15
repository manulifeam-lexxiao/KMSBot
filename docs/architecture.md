# KMSBot 系统架构总览

> Confluence 知识库智能问答系统 — 从数据同步到 AI 生成答案的全栈架构

---

## 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              入口层 Entry Layer                             │
│                                                                             │
│    ┌──────────┐    ┌──────────────┐    ┌──────────────┐                    │
│    │  浏览器   │    │  API 客户端   │    │  Dev CLI     │                    │
│    │  React   │    │  curl/httpx  │    │  npm run dev │                    │
│    └────┬─────┘    └──────┬───────┘    └──────┬───────┘                    │
│         └────────────────┬┘───────────────────┘                            │
└──────────────────────────┼─────────────────────────────────────────────────┘
                           │
┌──────────────────────────┼─────────────────────────────────────────────────┐
│                    网关层 Gateway Layer                                      │
│                                                                             │
│    ┌─────────────────────┴────────────────────────┐                        │
│    │              Nginx 反向代理 (:80)              │                        │
│    │  /          → 静态文件 (React SPA)            │                        │
│    │  /api/*     → Backend (:8000)                │                        │
│    └─────────────────────┬────────────────────────┘                        │
└──────────────────────────┼─────────────────────────────────────────────────┘
                           │
          ┌────────────────┴──────────────────┐
          ▼                                   ▼
┌─────────────────────┐          ┌────────────────────────────────────────────┐
│   前端层 Frontend    │          │               后端层 Backend               │
│                     │          │                                            │
│  React 18 + TS     │          │  ┌──────────────────────────────────────┐  │
│  Vite 6            │          │  │       API 路由层 FastAPI Router       │  │
│  React Router v7   │          │  │  /query  /health  /sync  /index     │  │
│                     │          │  │  /settings/*                        │  │
│  ┌───────────────┐ │          │  └──────────────┬───────────────────────┘  │
│  │  ChatPage     │ │  POST    │                 │                          │
│  │  ├ MessageList│ │ ──────── │  ┌──────────────▼───────────────────────┐  │
│  │  ├ ChatInput  │ │ /api/*   │  │      核心编排层 Orchestration         │  │
│  │  ├ AnswerMsg  │ │          │  │                                      │  │
│  │  ├ ThinkProg  │ │ SSE ◄──  │  │  QueryOrchestratorService           │  │
│  │  ├ SourceList │ │          │  │  ├ normalize → plan → search        │  │
│  │  ├ RelatedDoc │ │          │  │  ├ deduplicate → cap → assemble     │  │
│  │  └ DebugPanel │ │          │  │  └ generate answer                  │  │
│  └───────────────┘ │          │  │                                      │  │
│                     │          │  │  ConfluenceSyncService               │  │
│  ┌───────────────┐ │          │  │  ├ full_sync / incremental_sync     │  │
│  │ SettingsPage  │ │          │  │  └ parse → chunk → index            │  │
│  │ ├ Provider    │ │          │  └──────────────┬───────────────────────┘  │
│  │ ├ QueryCfg   │ │          │                 │                          │
│  │ ├ Thinking   │ │          │  ┌──────────────▼───────────────────────┐  │
│  │ ├ Sync/Index │ │          │  │     服务路由层 Provider Routers       │  │
│  │ ├ Health     │ │          │  │                                      │  │
│  │ └ TokenUsage │ │          │  │  SearchProviderRouter ──────┐        │  │
│  └───────────────┘ │          │  │    ├→ SQLiteFTSSearch      │运行时   │  │
│                     │          │  │    └→ AzureAISearch        │切换    │  │
│  ┌───────────────┐ │          │  │                             │        │  │
│  │  Hooks 层     │ │          │  │  ProviderAnswerRouter ─────┘        │  │
│  │  useQueryChat │ │          │  │    ├→ AzureOpenAI                   │  │
│  │  useSettings  │ │          │  │    └→ GitHubModels                  │  │
│  │  useProvider  │ │          │  └──────────────┬───────────────────────┘  │
│  │  useTokenUsage│ │          │                 │                          │
│  └───────────────┘ │          │  ┌──────────────▼───────────────────────┐  │
│                     │          │  │        基础服务层 Core Services       │  │
│  ┌───────────────┐ │          │  │                                      │  │
│  │  API 客户端层  │ │          │  │  QueryPlannerService  (AI 意图分析)  │  │
│  │  queryApi     │ │          │  │  TitleSearchService   (标题快速检索)  │  │
│  │  settingsApi  │ │          │  │  ConfluenceParseService (HTML 清洗)  │  │
│  │  operationsApi│ │          │  │  ConfluenceChunkService (文档切块)   │  │
│  │  + Mock 模式  │ │          │  │  HtmlCleaner          (BS4 解析)    │  │
│  └───────────────┘ │          │  └──────────────┬───────────────────────┘  │
└─────────────────────┘          │                 │                          │
                                 │  ┌──────────────▼───────────────────────┐  │
                                 │  │       数据仓库层 Repositories         │  │
                                 │  │                                      │  │
                                 │  │  DocumentRegistryRepository          │  │
                                 │  │  TokenUsageRepository                │  │
                                 │  │  BaseRepository (通用 CRUD)          │  │
                                 │  └──────────────┬───────────────────────┘  │
                                 │                 │                          │
                                 │  ┌──────────────▼───────────────────────┐  │
                                 │  │       基础设施层 Infrastructure       │  │
                                 │  │                                      │  │
                                 │  │  ServiceContainer  (依赖注入)        │  │
                                 │  │  Settings / YAML   (配置管理)        │  │
                                 │  │  SQLiteDatabase    (连接/迁移)       │  │
                                 │  │  Logging           (JSON/KV 日志)    │  │
                                 │  │  ErrorHandler      (统一错误处理)    │  │
                                 │  └──────────────────────────────────────┘  │
                                 └────────────────────────────────────────────┘
                                                   │
┌──────────────────────────────────────────────────┼──────────────────────────┐
│                          存储层 Storage Layer      │                         │
│                                                   │                         │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────▼──────┐  ┌───────────┐  │
│  │   SQLite DB   │  │  文件系统     │  │  Prompt 模板     │  │  配置文件  │  │
│  │              │  │              │  │                  │  │           │  │
│  │ document_    │  │ data/raw/    │  │ query_answering/ │  │ app.yaml  │  │
│  │  registry    │  │ data/cleaned/│  │ query_planning/  │  │           │  │
│  │ token_usage  │  │ data/chunks/ │  │ query_rewrite/   │  │           │  │
│  │ chunks_fts   │  │ data/logs/   │  │                  │  │           │  │
│  │ titles_fts   │  │              │  │                  │  │           │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  └───────────┘  │
└───────────────────────────────────────────────────────────────────────────────┘
                                                   │
┌──────────────────────────────────────────────────┼──────────────────────────┐
│                        外部服务层 External Services │                         │
│                                                   │                         │
│  ┌────────────────┐  ┌────────────────┐  ┌───────┴────────┐               │
│  │   Confluence    │  │  Azure OpenAI   │  │  Azure AI      │               │
│  │   Cloud API     │  │  Chat API       │  │  Search        │               │
│  │                │  │                │  │                │               │
│  │  知识源同步     │  │  答案生成       │  │  BM25 检索      │               │
│  │  REST API      │  │  GPT-4o 系列   │  │  全文索引       │               │
│  └────────────────┘  └────────────────┘  └────────────────┘               │
│                                                                             │
│  ┌────────────────┐  ┌────────────────┐                                    │
│  │  GitHub Models  │  │  SQLite FTS5    │                                    │
│  │  Chat API       │  │  (本地替代)     │                                    │
│  │                │  │                │                                    │
│  │  备选 LLM 提供  │  │  本地全文检索   │                                    │
│  └────────────────┘  └────────────────┘                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 分层说明

### 1. 入口层

| 入口 | 说明 |
|------|------|
| 浏览器 | React SPA，用户通过 Chat UI 提问 |
| API 客户端 | 通过 HTTP 直接调用 `/api/*` 端点 |
| Dev CLI | `npm run dev` 启动前后端开发服务器 |

### 2. 网关层

Nginx 作为统一入口，将静态资源请求和 API 请求分发到不同后端。生产环境通过 Docker Compose 部署。

### 3. 前端层

| 模块 | 技术 | 职责 |
|------|------|------|
| ChatPage | React + CSS | 问答对话界面，支持 SSE 流式响应 |
| SettingsPage | React + CSS | 运维管理：提供者切换、同步、索引、健康检查 |
| Hooks | React Hooks | 状态管理：`useQueryChat`, `useSettings`, `useProvider` 等 |
| API 客户端 | Fetch + SSE | 封装所有后端调用，支持 Mock 模式独立开发 |

### 4. 后端 — API 路由层

FastAPI 路由，统一 `/api` 前缀：

| 端点 | 方法 | 职责 |
|------|------|------|
| `/api/query` | POST | 提交查询，返回答案+来源（支持 SSE 流式） |
| `/api/health` | GET | 服务健康状态 |
| `/api/sync/full` | POST | 触发全量 Confluence 同步（202 异步） |
| `/api/sync/incremental` | POST | 触发增量同步 |
| `/api/sync/status` | GET | 同步状态查询 |
| `/api/index/rebuild` | POST | 触发索引重建（202 异步） |
| `/api/index/status` | GET | 索引状态查询 |
| `/api/settings/*` | GET/POST | 提供者切换、查询参数、THINKING 模式配置 |

### 5. 后端 — 核心编排层

**QueryOrchestratorService** — 查询主管道：

```
用户查询 → normalize → QueryPlanner (AI 意图分析)
         → Search (全文检索) → 去重 → 截断 → 组装上下文
         → LLM 生成答案 → 返回 answer + sources + debug
```

支持四种查询模式：

| 模式 | 说明 |
|------|------|
| Standard | 直接检索 → 生成 |
| THINKING | AI 规划 → 标题搜索 → 深度阅读 → 逐步 SSE 流式返回 |
| Meta Query | 返回知识库统计信息 |
| General Chat | 非知识查询的日常对话回退 |

**ConfluenceSyncService** — 数据同步管道：

```
Confluence API → 拉取页面 → 保存 raw HTML
    → HtmlCleaner (BS4 清洗) → CleanedDocument
    → ConfluenceChunkService (切块) → ChunkRecord[]
    → 写入索引 (FTS5 / Azure AI Search)
    → 更新 DocumentRegistry
```

### 6. 后端 — 服务路由层

运行时动态切换底层实现，无需重启：

| Router | 实现 A | 实现 B |
|--------|--------|--------|
| SearchProviderRouter | SQLite FTS5（本地） | Azure AI Search（云端） |
| ProviderAnswerRouter | Azure OpenAI | GitHub Models |

### 7. 后端 — 基础服务层

| 服务 | 职责 |
|------|------|
| QueryPlannerService | 调用 LLM 分析查询意图，生成搜索关键词和标签过滤 |
| TitleSearchService | FTS5 标题快速匹配，服务于 THINKING 模式 |
| ConfluenceParseService | HTML → 结构化 CleanedDocument |
| ConfluenceChunkService | CleanedDocument → 可搜索的 ChunkRecord |
| HtmlCleaner | BeautifulSoup 清洗：去噪、提取段落结构 |

### 8. 后端 — 数据仓库层

Repository 模式封装数据库操作：

| Repository | 表 | 职责 |
|------------|---|------|
| DocumentRegistryRepository | `document_registry` | 文档元数据（page_id, 标题, chunk 数, 索引状态） |
| TokenUsageRepository | `token_usage` | LLM Token 用量追踪 |

### 9. 后端 — 基础设施层

| 组件 | 职责 |
|------|------|
| ServiceContainer | 依赖注入容器，启动时构建所有服务实例 |
| Settings (Pydantic + YAML) | 多层配置：YAML 文件 + `KMSBOT_*` 环境变量覆盖 |
| SQLiteDatabase | 连接管理、自动迁移 |
| Logging | JSON/KV 格式日志，请求 ID 追踪 |
| ErrorHandler | 统一异常处理，结构化错误响应 |

### 10. 存储层

| 存储 | 内容 |
|------|------|
| SQLite DB | `document_registry`, `token_usage`, `chunks_fts`, `titles_fts` |
| 文件系统 | `data/raw/` (原始 HTML), `data/cleaned/` (清洗 JSON), `data/chunks/` (分块 JSON), `data/logs/` |
| Prompt 模板 | `prompts/query_answering/`, `query_planning/`, `query_rewrite/` |
| 配置文件 | `config/app.yaml` |

### 11. 外部服务层

| 服务 | 用途 | 认证方式 |
|------|------|---------|
| Confluence Cloud | 知识源同步 | Basic Auth (用户名 + API Token) |
| Azure OpenAI | 答案生成 (GPT-4o) | API Key 或 Azure AD |
| Azure AI Search | BM25 全文检索 | API Key |
| GitHub Models | 备选 LLM 提供者 | Bearer Token (PAT) |
| SQLite FTS5 | 本地全文检索替代方案 | 无需认证 |

---

## 部署架构

```
┌─── Docker Compose ──────────────────────────────────────┐
│                                                          │
│  ┌──────────────────┐      ┌──────────────────────┐     │
│  │  frontend (:80)  │      │  backend (:8000)     │     │
│  │  Nginx + React   │ ───► │  Uvicorn + FastAPI   │     │
│  │  SPA 静态文件     │ /api │  Python 3.11-slim   │     │
│  └──────────────────┘      └──────────┬───────────┘     │
│                                       │                  │
│                              ┌────────▼────────┐        │
│                              │   挂载卷          │        │
│                              │  ./data (读写)    │        │
│                              │  ./config (只读)  │        │
│                              └─────────────────┘        │
└──────────────────────────────────────────────────────────┘
```

- **后端健康检查**: `GET /api/health`，30s 间隔
- **前端启动条件**: 等待后端健康检查通过
- **API 代理超时**: 120s（支持长时间 THINKING 查询）

---

## 数据库 Schema

### document_registry

```sql
page_id           TEXT PRIMARY KEY     -- Confluence 页面 ID
title             TEXT NOT NULL        -- 页面标题
source_version    INTEGER NOT NULL     -- 来源版本号
last_updated      TEXT NOT NULL        -- 最后更新时间
raw_hash          TEXT NOT NULL        -- 原始内容哈希
chunk_count       INTEGER DEFAULT 0    -- 分块数量
pipeline_version  INTEGER NOT NULL     -- 处理管道版本
index_status      TEXT                 -- not_indexed|pending|indexed|stale|error
last_sync_time    TEXT                 -- 最后同步时间
last_index_time   TEXT                 -- 最后索引时间
labels            TEXT DEFAULT '[]'    -- JSON 标签数组
```

### token_usage

```sql
id                INTEGER PRIMARY KEY  -- 自增 ID
timestamp         TEXT NOT NULL        -- 记录时间
query             TEXT NOT NULL        -- 用户查询
mode              TEXT                 -- standard|thinking
provider          TEXT NOT NULL        -- LLM 提供者
stage             TEXT                 -- planning|ranking|answering|summarizing
prompt_tokens     INTEGER DEFAULT 0    -- 输入 Token 数
completion_tokens INTEGER DEFAULT 0    -- 输出 Token 数
model             TEXT                 -- 模型名称
```

### FTS5 虚拟表

- **chunks_fts**: 全文搜索索引，存储所有文档分块
- **titles_fts**: 标题搜索索引，用于 THINKING 模式快速标题匹配

---

## 设计模式

| 模式 | 应用位置 |
|------|---------|
| 依赖注入 | ServiceContainer + FastAPI Depends() |
| Repository | BaseRepository → DocumentRegistryRepo / TokenUsageRepo |
| 策略模式 | SearchService / AnswerService 接口，支持多实现 |
| 路由模式 | SearchProviderRouter / ProviderAnswerRouter 运行时切换 |
| 管道模式 | 查询编排 (normalize → plan → search → postprocess → generate) |
| 工厂模式 | build_service_container() 构建所有服务实例 |
| 适配器模式 | AzureSearchClient / AzureOpenAIClient 封装外部 SDK |
| 状态机 | _SyncState / _IndexState 管理异步任务状态 |

---

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | React 18, TypeScript 5.6, Vite 6, React Router 7 |
| 后端 | Python 3.11, FastAPI, Uvicorn, Pydantic v2 |
| 数据库 | SQLite + FTS5 |
| HTTP 客户端 | httpx (异步) |
| HTML 解析 | BeautifulSoup4 |
| 搜索 | Azure AI Search (BM25) / SQLite FTS5 |
| LLM | Azure OpenAI / GitHub Models |
| 知识源 | Confluence Cloud REST API |
| 部署 | Docker Compose, Nginx 反向代理 |
| 测试 | pytest (后端), Vitest + React Testing Library (前端) |
| 代码质量 | Ruff (Python), ESLint + Prettier (TypeScript) |
