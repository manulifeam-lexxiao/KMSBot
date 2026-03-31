"""Thin wrapper around the Azure OpenAI chat-completions API.

Encapsulates HTTP transport so the answer generator service never
touches ``httpx`` directly and can be easily stubbed in tests.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

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


class AzureOpenAIClient:
    """Low-level client for Azure OpenAI chat completions.

    Uses ``httpx.AsyncClient`` with the ``api-key`` header required by
    the Azure OpenAI REST API.
    """

    _API_VERSION = "2024-06-01"

    def __init__(
        self,
        *,
        endpoint: str,
        api_key: str,
        chat_deployment: str,
        timeout: float = 30.0,
    ) -> None:
        self._endpoint = endpoint.rstrip("/")
        self._chat_deployment = chat_deployment
        self._url = (
            f"{self._endpoint}/openai/deployments/{self._chat_deployment}"
            f"/chat/completions?api-version={self._API_VERSION}"
        )
        self._client = httpx.AsyncClient(
            headers={"api-key": api_key, "Content-Type": "application/json"},
            timeout=timeout,
        )

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> ChatCompletionResult:
        """Send a chat-completion request and return the first choice."""
        body = {
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        logger.debug(
            "Azure OpenAI request – deployment=%s  messages=%d",
            self._chat_deployment,
            len(messages),
        )
        response = await self._client.post(self._url, json=body)
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
