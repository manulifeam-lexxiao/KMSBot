"""冒烟集成测试 – 验证完整 FastAPI 应用可以启动并响应所有 API 端点。

不需要真实的 Confluence / Azure 账号；所有外部依赖均通过 Placeholder 服务替代。
运行方式：
    cd backend
    pytest tests/test_smoke_integration.py -v
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from kms_bot.app import create_app
from kms_bot.core.settings import ApplicationSettings

# 项目根目录（backend/ 的上一级）
_REPO_ROOT = Path(__file__).resolve().parents[2]


# ── fixture：使用临时目录构建最小配置 ─────────────────────────


@pytest.fixture(scope="module")
def app(tmp_path_factory: pytest.TempPathFactory):
    """构建使用 Placeholder 服务的 FastAPI 应用实例。"""
    tmp = tmp_path_factory.mktemp("smoke")
    for subdir in ("raw", "cleaned", "chunks", "sqlite", "logs"):
        (tmp / subdir).mkdir()

    settings = ApplicationSettings(
        app={"env": "test", "debug": True, "pipeline_version": 1},
        storage={
            "data_root": str(tmp),
            "raw_dir": str(tmp / "raw"),
            "cleaned_dir": str(tmp / "cleaned"),
            "chunks_dir": str(tmp / "chunks"),
            "sqlite_dir": str(tmp / "sqlite"),
            "logs_dir": str(tmp / "logs"),
        },
        database={"url": f"sqlite:///{tmp}/sqlite/kmsbot.db"},
        # 不提供 confluence / search / answer 凭据 → 均使用 Placeholder
        confluence={"base_url": "", "space_key": "", "username": "", "api_token": ""},
        search={"endpoint": "", "api_key": "", "index_name": "kmsbot-chunks"},
        answer={"endpoint": "", "api_key": "", "chat_deployment": ""},
    )
    # 使用实际项目根（保证 config/contracts/sqlite/001_registry.sql 可被找到）
    settings.bind_runtime_paths(repo_root=_REPO_ROOT, config_file_path=_REPO_ROOT / "config" / "app.example.yaml")
    return create_app(settings)


@pytest.fixture(scope="module")
def client(app):
    with TestClient(app) as c:
        yield c


# ── 健康检查 ──────────────────────────────────────────────────


def test_health_returns_200(client: TestClient) -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] in ("ok", "degraded")
    assert "dependencies" in body


# ── 同步端点 ──────────────────────────────────────────────────


def test_full_sync_returns_400_without_confluence(client: TestClient) -> None:
    """未配置 Confluence 时，full sync 应返回 400（非 5xx）。"""
    resp = client.post("/api/sync/full")
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "confluence_not_configured"


def test_incremental_sync_returns_400_without_confluence(client: TestClient) -> None:
    resp = client.post("/api/sync/incremental")
    assert resp.status_code == 400


def test_sync_status_returns_200(client: TestClient) -> None:
    resp = client.get("/api/sync/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] in ("idle", "running", "success", "error")


# ── 索引端点 ──────────────────────────────────────────────────


def test_index_rebuild_accepted_with_placeholder(client: TestClient) -> None:
    """Placeholder search 服务应接受重建请求（202）。"""
    resp = client.post("/api/index/rebuild")
    assert resp.status_code == 202
    assert resp.json()["status"] == "accepted"


def test_index_status_returns_200(client: TestClient) -> None:
    resp = client.get("/api/index/status")
    assert resp.status_code == 200
    body = resp.json()
    assert "status" in body


# ── 查询端点 ──────────────────────────────────────────────────


def test_query_returns_answer(client: TestClient) -> None:
    """即使是 Placeholder 实现，query 端点也应返回结构正确的响应。"""
    resp = client.post(
        "/api/query",
        json={"query": "how do I reset access?", "top_k": 5, "include_debug": False},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "answer" in body
    assert "sources" in body
    assert isinstance(body["sources"], list)


def test_query_rejects_empty_string(client: TestClient) -> None:
    resp = client.post("/api/query", json={"query": "", "top_k": 5, "include_debug": False})
    # 空查询应被拒绝（400 或 422）
    assert resp.status_code in (400, 422)


def test_query_rejects_missing_field(client: TestClient) -> None:
    resp = client.post("/api/query", json={})
    assert resp.status_code == 422
