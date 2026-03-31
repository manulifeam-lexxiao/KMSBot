# KMS Bot 运行手册

本手册覆盖从零开始到首次问答的完整操作流程，包括本地开发启动和 Docker 部署两种模式。

---

## 一、环境准备

### 前提条件

| 工具 | 最低版本 | 用途 |
|------|----------|------|
| Python | 3.11 | 后端运行 |
| Node.js | 20 | 前端构建 |
| Docker + Compose | 24 | 容器部署（可选） |

### 克隆与配置

```bash
git clone <repo-url>
cd KMSBot

# 复制配置文件
cp config/app.example.yaml config/app.yaml
cp .env.example .env
```

编辑 `.env`，填入以下凭据（留空则使用 Placeholder 模式，不影响启动）：

```
KMSBOT_CONFLUENCE_BASE_URL=https://your-org.atlassian.net/wiki
KMSBOT_CONFLUENCE_SPACE_KEY=KMS
KMSBOT_CONFLUENCE_USERNAME=user@example.com
KMSBOT_CONFLUENCE_API_TOKEN=<token>

KMSBOT_AZURE_SEARCH_ENDPOINT=https://xxx.search.windows.net
KMSBOT_AZURE_SEARCH_KEY=<admin-key>

KMSBOT_AZURE_OPENAI_ENDPOINT=https://xxx.openai.azure.com
KMSBOT_AZURE_OPENAI_API_KEY=<api-key>
KMSBOT_AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o
```

---

## 二、本地开发启动

### 后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

# 从项目根目录启动（保证提示词模板路径正确）
cd ..
set PYTHONPATH=backend/src      # Windows
# export PYTHONPATH=backend/src # macOS/Linux

uvicorn kms_bot.main:app --reload --host 0.0.0.0 --port 8000
```

后端健康检查：`http://localhost:8000/api/health`

### 前端

```bash
cd frontend
npm install
npm run dev
```

前端地址：`http://localhost:5173`（自动代理 `/api` 到 `localhost:8000`）

---

## 三、Docker 部署

```bash
# 在项目根目录执行
docker compose up --build -d

# 查看日志
docker compose logs -f backend

# 停止
docker compose down
```

服务地址：
- 前端：`http://localhost`（80 端口）
- 后端 API：`http://localhost:8000/api`（直接访问）

> **注意**：`.env` 文件必须存在于项目根目录，`data/` 目录会被挂载到容器内以持久化数据。

---

## 四、首次完整同步

```bash
# 触发全量同步（异步后台任务：拉取 → 解析 → 分块）
curl -X POST http://localhost:8000/api/sync/full

# 轮询同步状态，直到 status=success
curl http://localhost:8000/api/sync/status
```

同步完成后，`data/raw/`、`data/cleaned/`、`data/chunks/` 目录会有对应产物。

---

## 五、索引重建

同步完成后需要将分块上传到 Azure AI Search：

```bash
# 触发索引重建（读取 data/chunks/ 上传到 Azure Search）
curl -X POST http://localhost:8000/api/index/rebuild

# 轮询索引状态
curl http://localhost:8000/api/index/status
```

---

## 六、增量同步

增量同步仅处理上次同步之后有更新的页面：

```bash
curl -X POST http://localhost:8000/api/sync/incremental
```

同步完成后仍需手动触发索引重建（`POST /api/index/rebuild`），以将新增分块推送到 Azure Search。

---

## 七、首次查询

索引就绪后，通过聊天 UI 或直接调用 API 进行问答：

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "how do I reset iPension access?"}'
```

响应结构：

```json
{
  "answer": "...",
  "sources": [{"title": "...", "url": "...", "section": "...", "doc_id": "...", "chunk_id": "..."}],
  "related_documents": [{"page_id": "...", "title": "...", "url": "..."}],
  "debug": {"normalized_query": "...", "selected_chunks": []}
}
```

---

## 八、冒烟测试

```bash
cd backend
pytest tests/test_smoke_integration.py -v
```

所有测试通过即表示各 API 端点可正常响应（无需真实云服务账号）。

---

## 九、常见问题排查

### 后端启动失败：`Config file does not exist`

原因：未复制配置文件。  
解决：`cp config/app.example.yaml config/app.yaml`

### 同步返回 400：`confluence_not_configured`

原因：`.env` 中 Confluence 凭据为空。  
解决：填入有效的 `KMSBOT_CONFLUENCE_BASE_URL`、`USERNAME`、`API_TOKEN`。

### 查询返回的 answer 为占位文本

原因：未配置 Azure OpenAI 或 Azure Search，系统使用 Placeholder 服务。  
解决：在 `.env` 中填入真实的 `KMSBOT_AZURE_OPENAI_*` 和 `KMSBOT_AZURE_SEARCH_*` 值。

### 索引重建后查询无结果

原因：可能 Azure Search 索引未收到数据，或 `data/chunks/` 目录为空。  
排查步骤：
1. 确认 `data/chunks/` 有 `.chunks.json` 文件
2. 检查后端日志 `data/logs/`
3. 确认 `GET /api/index/status` 返回 `status=success`

### Docker 构建失败：前端依赖下载超时

解决：配置国内 npm 镜像，或在 `Dockerfile.frontend` 中添加：
```dockerfile
RUN npm config set registry https://registry.npmmirror.com
```

---

## 十、模块依赖图

```
Confluence API
      │
      ▼
 SyncService          ← ConfluenceClient
      │  (拉取后自动触发)
      ▼
 ParseService         ← data/raw/*.html + *.meta.json
      │
      ▼
 ChunkService         ← data/cleaned/*.json
      │
      ▼  (手动触发)
 SearchService        ← data/chunks/*.chunks.json → Azure AI Search
      │
      ▼
 QueryService         ← SearchService + AnswerService
      │
      ▼
 POST /api/query      ← 前端 ChatPage
```
