# Docker 部署

本目录包含所有容器化部署相关的资产。

## 文件说明

| 文件 | 说明 |
|------|------|
| `Dockerfile.backend` | Python 3.11-slim 后端镜像 |
| `Dockerfile.frontend` | 多阶段构建前端静态资源，由 Nginx 托管 |
| `nginx.conf` | Nginx 配置，静态文件服务 + `/api` 反向代理 |

docker-compose.yml 位于仓库根目录。

## 启动服务

```bash
# 在仓库根目录执行
docker compose up --build
```

| 服务 | 对外端口 |
|------|---------|
| 前端（Nginx） | `http://localhost` |
| 后端（FastAPI） | `http://localhost:8000` |

## 配置挂载

- `./config:/app/config:ro`：将本地 `config/app.yaml` 只读挂载到容器，无需重建镜像即可修改配置。
- `./data:/app/data`：持久化所有运行时数据（raw / cleaned / chunks / sqlite / logs）。

## 注意事项

- 不在 Dockerfile 或 compose 文件中硬编码任何密钥或凭据。
- 敏感配置通过 `config/app.yaml` 文件或 `.env` 环境变量注入（docker-compose 通过 `env_file: .env` 加载）。
