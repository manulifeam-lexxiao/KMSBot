from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from kms_bot import __version__

ConfigValueParser = Callable[[str], Any]


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"Unsupported boolean value: {value}")


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _resolve_path(root: Path, raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    return (root / candidate).resolve()


def _read_yaml_config(config_file_path: Path) -> dict[str, Any]:
    if not config_file_path.exists():
        raise FileNotFoundError(f"Config file does not exist: {config_file_path}")

    with config_file_path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}

    if not isinstance(loaded, dict):
        raise ValueError("YAML config root must be an object.")

    return loaded


def _set_nested_value(target: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    cursor = target
    for key in path[:-1]:
        next_value = cursor.get(key)
        if not isinstance(next_value, dict):
            next_value = {}
            cursor[key] = next_value
        cursor = next_value
    cursor[path[-1]] = value


ENVIRONMENT_OVERRIDES: tuple[tuple[str, tuple[str, ...], ConfigValueParser], ...] = (
    ("KMSBOT_ENV", ("app", "env"), str),
    ("KMSBOT_DEBUG", ("app", "debug"), _parse_bool),
    ("KMSBOT_PIPELINE_VERSION", ("app", "pipeline_version"), int),
    ("KMSBOT_HOST", ("server", "host"), str),
    ("KMSBOT_PORT", ("server", "port"), int),
    ("KMSBOT_LOG_LEVEL", ("logging", "level"), str),
    ("KMSBOT_DATA_ROOT", ("storage", "data_root"), str),
    ("KMSBOT_DATABASE_URL", ("database", "url"), str),
    ("KMSBOT_CONFLUENCE_BASE_URL", ("confluence", "base_url"), str),
    ("KMSBOT_CONFLUENCE_SPACE_KEY", ("confluence", "space_key"), str),
    ("KMSBOT_CONFLUENCE_USERNAME", ("confluence", "username"), str),
    ("KMSBOT_CONFLUENCE_API_TOKEN", ("confluence", "api_token"), str),
    ("KMSBOT_SEARCH_PROVIDER", ("search", "provider"), str),
    ("KMSBOT_AZURE_SEARCH_ENDPOINT", ("search", "endpoint"), str),
    ("KMSBOT_AZURE_SEARCH_KEY", ("search", "api_key"), str),
    ("KMSBOT_AZURE_SEARCH_INDEX_NAME", ("search", "index_name"), str),
    ("KMSBOT_AZURE_OPENAI_ENDPOINT", ("answer", "endpoint"), str),
    ("KMSBOT_AZURE_OPENAI_API_KEY", ("answer", "api_key"), str),
    ("KMSBOT_AZURE_OPENAI_CHAT_DEPLOYMENT", ("answer", "chat_deployment"), str),
    ("KMSBOT_ANSWER_PROVIDER", ("answer", "provider"), str),
    ("KMSBOT_AZURE_OPENAI_SSL_VERIFY", ("answer", "ssl_verify"), _parse_bool),
    ("KMSBOT_AZURE_AD_TENANT_ID", ("answer", "tenant_id"), str),
    ("KMSBOT_AZURE_AD_CLIENT_ID", ("answer", "client_id"), str),
    ("KMSBOT_AZURE_AD_CLIENT_SECRET", ("answer", "client_secret"), str),
    ("KMSBOT_GITHUB_MODELS_API_TOKEN", ("github_models", "api_token"), str),
    ("KMSBOT_GITHUB_MODELS_MODEL_NAME", ("github_models", "model_name"), str),
    ("KMSBOT_QUERY_TOP_K", ("query", "top_k"), int),
    ("KMSBOT_QUERY_INCLUDE_DEBUG", ("query", "include_debug"), _parse_bool),
    ("KMSBOT_PROMPT_QUERY_ANSWERING", ("prompts", "query_answering"), str),
    ("KMSBOT_PROMPT_QUERY_REWRITE", ("prompts", "query_rewrite"), str),
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class AppSettings(StrictModel):
    name: str = "kms-bot"
    env: str = "local"
    debug: bool = False
    pipeline_version: int = Field(default=1, ge=1)
    version: str = __version__


class ServerSettings(StrictModel):
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    api_prefix: str = "/api"


class LoggingSettings(StrictModel):
    level: str = "INFO"
    json_logs: bool = Field(default=False, alias="json")


class StorageSettings(StrictModel):
    data_root: str = "./data"
    raw_dir: str = "./data/raw"
    cleaned_dir: str = "./data/cleaned"
    chunks_dir: str = "./data/chunks"
    sqlite_dir: str = "./data/sqlite"
    logs_dir: str = "./data/logs"


class DatabaseSettings(StrictModel):
    url: str = "sqlite:///./data/sqlite/kmsbot.db"


class ConfluenceSettings(StrictModel):
    base_url: str = ""
    space_key: str = ""
    username: str = ""
    api_token: str = ""
    page_limit: int = Field(default=25, ge=1, le=100)

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url and self.space_key and self.username and self.api_token)


class SearchSettings(StrictModel):
    provider: Literal["azure_ai_search", "sqlite_fts5"] = "azure_ai_search"
    endpoint: str = ""
    api_key: str = ""
    index_name: str = "kmsbot-chunks"

    @property
    def is_configured(self) -> bool:
        if self.provider == "sqlite_fts5":
            return True
        return bool(self.endpoint and self.api_key and self.index_name)


class AnswerSettings(StrictModel):
    provider: Literal["azure_openai", "github_models"] = "azure_openai"
    endpoint: str = ""
    api_key: str = ""
    # Azure 原生端点用 "api-key"；APIM 网关用 "Ocp-Apim-Subscription-Key"
    api_key_header: str = "api-key"
    chat_deployment: str = ""
    ssl_verify: bool = True
    # Azure AD 客户端凭据（APIM 网关需要 Bearer Token + 订阅密钒双重认证时填写）
    tenant_id: str = ""
    client_id: str = ""
    client_secret: str = ""
    scope: str = "https://cognitiveservices.azure.com/.default"

    @property
    def use_aad_auth(self) -> bool:
        """True 表示需要先用 client credentials 换 Bearer token。"""
        return bool(self.tenant_id and self.client_id and self.client_secret)

    @property
    def is_configured(self) -> bool:
        return bool(self.endpoint and self.chat_deployment and (self.api_key or self.use_aad_auth))


class GithubModelsSettings(StrictModel):
    api_token: str = ""
    model_name: str = "gpt-4o"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_token and self.model_name)


class QuerySettings(StrictModel):
    top_k: int = Field(default=5, ge=1, le=10)
    include_debug: bool = False
    max_chunks_per_doc: int = Field(default=3, ge=1, le=10)
    similarity_threshold: float = Field(default=0.85, ge=0.0, le=1.0)


class PromptSettings(StrictModel):
    query_answering: str = "prompts/query_answering/default.md"
    query_rewrite: str = "prompts/query_rewrite/default.md"


class ApplicationSettings(StrictModel):
    app: AppSettings = Field(default_factory=AppSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    confluence: ConfluenceSettings = Field(default_factory=ConfluenceSettings)
    search: SearchSettings = Field(default_factory=SearchSettings)
    answer: AnswerSettings = Field(default_factory=AnswerSettings)
    github_models: GithubModelsSettings = Field(default_factory=GithubModelsSettings)
    query: QuerySettings = Field(default_factory=QuerySettings)
    prompts: PromptSettings = Field(default_factory=PromptSettings)

    _repo_root: Path = PrivateAttr(default_factory=_repository_root)
    _config_file_path: Path = PrivateAttr(
        default_factory=lambda: _repository_root() / "config/app.example.yaml"
    )

    def bind_runtime_paths(self, repo_root: Path, config_file_path: Path) -> ApplicationSettings:
        self._repo_root = repo_root
        self._config_file_path = config_file_path
        return self

    @property
    def repo_root(self) -> Path:
        return self._repo_root

    @property
    def config_file_path(self) -> Path:
        return self._config_file_path

    def resolve_path(self, raw_path: str) -> Path:
        return _resolve_path(self._repo_root, raw_path)

    @property
    def data_directories(self) -> tuple[Path, ...]:
        return (
            self.resolve_path(self.storage.data_root),
            self.resolve_path(self.storage.raw_dir),
            self.resolve_path(self.storage.cleaned_dir),
            self.resolve_path(self.storage.chunks_dir),
            self.resolve_path(self.storage.sqlite_dir),
            self.resolve_path(self.storage.logs_dir),
        )


def load_settings(config_file: str | None = None) -> ApplicationSettings:
    repo_root = _repository_root()
    env_path = os.getenv("KMSBOT_CONFIG_FILE")
    if config_file:
        raw_config_path = config_file
    elif env_path:
        raw_config_path = env_path
    elif (repo_root / "config/app.yaml").exists():
        raw_config_path = "config/app.yaml"
    else:
        raw_config_path = "config/app.example.yaml"
    config_file_path = _resolve_path(repo_root, raw_config_path)

    raw_settings = _read_yaml_config(config_file_path)

    for env_name, path, parser in ENVIRONMENT_OVERRIDES:
        raw_value = os.getenv(env_name)
        if raw_value is None:
            continue
        _set_nested_value(raw_settings, path, parser(raw_value))

    settings = ApplicationSettings.model_validate(raw_settings)
    return settings.bind_runtime_paths(repo_root=repo_root, config_file_path=config_file_path)
