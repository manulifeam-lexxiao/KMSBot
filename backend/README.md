# 后端（Backend）

Python 3.11 + FastAPI 后端服务，负责 Confluence 同步、文档清洗、分块、Azure AI Search 索引写入，以及查询编排与答案生成。

## 包根路径

```text
backend/src/kms_bot/
```

## 目录结构

```text
backend/
  src/
    kms_bot/
      api/
        router.py          # 顶层路由聚合
        routes/
          health.py        # GET /api/health
          index.py         # POST /api/index（触发同步+索引）
          query.py         # POST /api/query（问答）
          settings.py      # GET/PUT /api/settings（运行时配置）
          sync.py          # POST /api/sync（仅同步）
      core/
        container.py       # 依赖注入容器
        dependencies.py    # FastAPI 依赖项
        errors.py          # 全局异常处理
        logging.py         # 日志配置与请求中间件
        settings.py        # 配置加载（YAML + 环境变量覆盖）
        utils.py           # 通用工具函数
      db/                  # SQLite 连接与初始化
      repositories/        # 持久化适配器
      schemas/             # Pydantic 请求/响应模型
      services/            # 共享服务接口与编排抽象
      modules/
        sync/              # Confluence 同步模块
        parser/            # HTML 清洗与结构化解析
        chunker/           # 文档分块与向量准备
        search/            # Azure AI Search 适配器
        query/             # 查询编排与上下文组装
        answer/            # Azure OpenAI / GitHub Models 答案生成
```

## 本地开发

```bash
# 在仓库根目录执行
pip install -r backend/requirements.txt

# 确保 config/app.yaml 存在且填写了必要凭据
uvicorn kms_bot.main:app --reload --port 8000
```

## 测试

```bash
pytest
```

测试文件位于 `backend/tests/`，覆盖清洗器、解析器、分块器、检索、问答编排和冒烟集成测试。

## 配置加载优先级

1. `config/app.yaml`（本地）或 `config/app.example.yaml`（默认回退）
2. 环境变量（`KMSBOT_*` 前缀，可覆盖 YAML 中任意配置项，详见根 `README.md`）
3. `KMSBOT_CONFIG_FILE` 环境变量可指定自定义配置文件路径

## 代码规范

- 文件名：`snake_case.py`
- 路由文件：`sync.py`、`index.py`、`query.py`、`health.py`
- 服务类：`SomethingService`
- 仓库类：`SomethingRepository`
- 请求模型：`SomethingRequest`
- 响应模型：`SomethingResponse`
- 路由层只处理 HTTP 请求/响应绑定，业务逻辑放在 `modules/` 或 `services/`。
