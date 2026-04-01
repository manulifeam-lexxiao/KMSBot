"""Thin wrapper around the Azure OpenAI chat-completions API.

Encapsulates HTTP transport so the answer generator service never
touches ``httpx`` directly and can be easily stubbed in tests.

支持两种认证模式：
1. API Key 模式（标准 Azure OpenAI 或 APIM 订阅密钥）
2. Azure AD 客户端凭据模式（APIM 网关需要 Bearer Token + 订阅密钥双重认证）
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ChatMessage:
    role: str  # "system" | "user"
    content: str


@dataclass(frozen=True, slots=True)
class ChatCompletionResult:
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int


@dataclass
class _TokenCache:
    """简单的内存 token 缓存，提前 60 秒刷新。"""

    access_token: str = ""
    expires_at: float = 0.0

    def is_valid(self) -> bool:
        return bool(self.access_token) and time.monotonic() < self.expires_at - 60


class AzureOpenAIClient:
    """Low-level client for Azure OpenAI chat completions.

    - API Key 模式：直接用 api_key_header 携带密钥。
    - AAD 模式：先用 client_credentials 换 Bearer token，再同时携带
      Authorization: Bearer {token} 和 Ocp-Apim-Subscription-Key。
      Token 请求走系统代理（与参考脚本行为一致），Chat 请求不走代理。
    """

    _API_VERSION = "2024-06-01"

    def __init__(
        self,
        *,
        endpoint: str,
        api_key: str,
        chat_deployment: str,
        timeout: float = 30.0,
        ssl_verify: bool = True,
        api_key_header: str = "api-key",
        # Azure AD 客户端凭据（可选）
        tenant_id: str = "",
        client_id: str = "",
        client_secret: str = "",
        scope: str = "https://cognitiveservices.azure.com/.default",
    ) -> None:
        self._endpoint = endpoint.rstrip("/")
        self._chat_deployment = chat_deployment
        self._api_key = api_key
        self._api_key_header = api_key_header
        self._ssl_verify = ssl_verify

        # Azure AD 凭据
        self._use_aad = bool(tenant_id and client_id and client_secret)
        self._tenant_id = tenant_id
        self._client_id = client_id
        self._client_secret = client_secret
        self._scope = scope
        self._token_url = (
            f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token" if tenant_id else ""
        )
        self._token_cache = _TokenCache()

        # URL 判断：endpoint 已是完整 /chat/completions 路径（自定义网关）直接使用
        if self._endpoint.endswith("/chat/completions"):
            self._url = self._endpoint
            self._full_url_mode = True
        else:
            self._url = (
                f"{self._endpoint}/openai/deployments/{self._chat_deployment}"
                f"/chat/completions?api-version={self._API_VERSION}"
            )
            self._full_url_mode = False

        # Chat 客户端：不走系统代理，SSL 可配置
        self._chat_client = httpx.AsyncClient(
            timeout=timeout,
            trust_env=False,
            verify=ssl_verify,
        )
        # Token 客户端：走系统代理（AAD 登录端点是公网地址）
        # ssl_verify 同步传入，应对公司代理做 SSL 拦截的场景
        self._token_client = httpx.AsyncClient(
            timeout=60.0,
            trust_env=True,
            verify=ssl_verify,
        )

    async def _get_access_token(self) -> str:
        """获取 Azure AD access token，带内存缓存。"""
        if self._token_cache.is_valid():
            return self._token_cache.access_token

        response = await self._token_client.post(
            self._token_url,
            data={
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "scope": self._scope,
                "grant_type": "client_credentials",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        payload = response.json()
        token = payload.get("access_token", "")
        expires_in = int(payload.get("expires_in", 3600))
        self._token_cache.access_token = token
        self._token_cache.expires_at = time.monotonic() + expires_in
        logger.info("aad_token_refreshed", extra={"expires_in": expires_in})
        return token

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float | None = None,
        max_completion_tokens: int | None = 1024,
    ) -> ChatCompletionResult:
        """Send a chat-completion request and return the first choice."""
        body: dict = {
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "model": self._chat_deployment,
        }
        if temperature is not None:
            body["temperature"] = temperature
        if max_completion_tokens is not None:
            body["max_completion_tokens"] = max_completion_tokens

        # 构建请求头
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._use_aad:
            access_token = await self._get_access_token()
            headers["Authorization"] = f"Bearer {access_token}"
            # 同时携带订阅密钥
            if self._api_key:
                headers[self._api_key_header] = self._api_key
        else:
            headers[self._api_key_header] = self._api_key

        logger.debug(
            "Azure OpenAI request – deployment=%s  messages=%d  aad=%s",
            self._chat_deployment,
            len(messages),
            self._use_aad,
        )
        response = await self._chat_client.post(self._url, json=body, headers=headers)
        response.raise_for_status()
        data = response.json()

        choice = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        result = ChatCompletionResult(
            content=choice,
            model=data.get("model", self._chat_deployment),
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
        )
        logger.info(
            "Azure OpenAI response – tokens prompt=%d completion=%d",
            result.prompt_tokens,
            result.completion_tokens,
        )
        return result

    async def close(self) -> None:
        await self._client.aclose()
