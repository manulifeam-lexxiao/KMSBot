# KMS Bot

KMS Bot 是一个基于 Confluence 知识库的智能问答系统 POC。它将 Confluence 页面同步、清洗、分块后写入 Azure AI Search 索引，并通过 Azure OpenAI（或 GitHub Models）回答用户提问，同时返回引用来源。

## 技术栈

| 层次 | 技术 |
|------|------|
| 后端 | Python 3.11 · FastAPI · SQLite · Uvicorn |
| 前端 | React 18 · TypeScript · Vite · Zustand |
| 检索 | Azure AI Search |
| 生成 | Azure OpenAI（`gpt-4o`）/ GitHub Models |
| 数据源 | Confluence Cloud REST API |
| 部署 | Docker · docker-compose · Nginx |

## 目录结构

```text
backend/   Python 后端包（FastAPI API 层 + 各功能模块）
frontend/  React + TypeScript 前端应用
config/    YAML 配置基线与 JSON Schema / OpenAPI 合约
data/      运行时本地数据（raw / cleaned / chunks / sqlite / logs）
docker/    Dockerfile 与 Nginx 配置
docs/      架构文档与实现提示词
prompts/   后端运行时 LLM 提示词模板
```

## 快速启动

### 方式一：Docker Compose（推荐）

```bash
# 1. 复制并填写配置文件
cp config/app.example.yaml config/app.yaml
# 编辑 config/app.yaml，填入 confluence / search / answer 三组凭据

# 2. 启动服务
docker compose up --build
```

启动后访问：
- 前端：`http://localhost`
- 后端 API：`http://localhost:8000/api`
- 健康检查：`http://localhost:8000/api/health`

### 方式二：本地开发模式

```bash
# 后端
cd backend
pip install -r requirements.txt
cp ../config/app.example.yaml ../config/app.yaml
# 编辑 config/app.yaml 填写凭据
uvicorn kms_bot.main:app --reload --port 8000

# 前端（新终端）
cd frontend
npm install
npm run dev   # http://localhost:5173
```

## 配置说明

所有配置通过 `config/app.yaml` 提供（需自行创建，参考 `config/app.example.yaml`）。  
敏感项也可通过以下环境变量覆盖，无需修改 YAML 文件：

| 环境变量 | 对应配置项 | 说明 |
|---------|-----------|------|
| `KMSBOT_CONFLUENCE_BASE_URL` | `confluence.base_url` | Confluence 实例地址 |
| `KMSBOT_CONFLUENCE_SPACE_KEY` | `confluence.space_key` | 要同步的空间 Key |
| `KMSBOT_CONFLUENCE_USERNAME` | `confluence.username` | Confluence 账号邮箱 |
| `KMSBOT_CONFLUENCE_API_TOKEN` | `confluence.api_token` | Confluence API Token |
| `KMSBOT_AZURE_SEARCH_ENDPOINT` | `search.endpoint` | Azure AI Search 端点 |
| `KMSBOT_AZURE_SEARCH_KEY` | `search.api_key` | Azure AI Search 管理密钥 |
| `KMSBOT_AZURE_SEARCH_INDEX_NAME` | `search.index_name` | 索引名称（默认 `kmsbot-chunks`）|
| `KMSBOT_AZURE_OPENAI_ENDPOINT` | `answer.endpoint` | Azure OpenAI 端点 |
| `KMSBOT_AZURE_OPENAI_API_KEY` | `answer.api_key` | Azure OpenAI API Key |
| `KMSBOT_AZURE_OPENAI_CHAT_DEPLOYMENT` | `answer.chat_deployment` | 部署名称（如 `gpt-4o`）|

> 使用 GitHub Models 作为答案提供者时，设置 `answer.provider: github_models` 并填写 `KMSBOT_GITHUB_MODELS_API_TOKEN`。

## 契约文件权威顺序

当文件内容有冲突时，按以下顺序以较高优先级为准：

1. `config/contracts/openapi.yaml`
2. `config/contracts/sqlite/001_registry.sql`
3. `config/contracts/schemas/*.schema.json`
4. `config/app.example.yaml`
5. `README.md`

## 开发规范

- 业务逻辑只存放在后端代码和 `prompts/` 提示词模板中，不写入前端或 Azure Portal。
- 不在 POC/V1 中实现 ACL、向量混合检索、重排序或 Agent 工作流。
- 生成的数据文件只写入 `data/` 目录，不提交到源码仓库。
- 分支命名格式：`<type>/pNN-<scope>`，例如 `feature/p03-confluence-sync`。
