"""GitHub Models API client for chat completions.

Uses the OpenAI-compatible REST API exposed at
``https://models.inference.ai.azure.com`` with a GitHub personal
access token (PAT) or GitHub App token as the secret bearer.

The response schema matches the OpenAI chat-completions format, so
the parsing logic is identical to :mod:`openai_client`.
"""

from __future__ import annotations

import logging

import httpx

from kms_bot.services.openai_client import ChatCompletionResult, ChatMessage

logger = logging.getLogger(__name__)

_GITHUB_MODELS_BASE_URL = "https://models.inference.ai.azure.com"


class GithubModelsClient:
    """Low-level client for GitHub Models chat completions.

    Wraps the ``/chat/completions`` endpoint of the GitHub Models
    inference API.  The wire format is OpenAI-compatible.
    """

    def __init__(
        self,
        *,
        api_token: str,
        model_name: str,
        timeout: float = 30.0,
    ) -> None:
        self._model_name = model_name
        self._client = httpx.AsyncClient(
            base_url=_GITHUB_MODELS_BASE_URL,
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> ChatCompletionResult:
        """Send a chat-completion request to GitHub Models."""
        body = {
            "model": self._model_name,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
        }
        if max_tokens is not None:
            body["max_tokens"] = max_tokens
        logger.debug(
            "GitHub Models request – model=%s  messages=%d",
            self._model_name,
            len(messages),
        )
        response = await self._client.post("/chat/completions", json=body)
        response.raise_for_status()
        data = response.json()

        choice = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        result = ChatCompletionResult(
            content=choice,
            model=data.get("model", self._model_name),
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
        )
        logger.info(
            "GitHub Models response – tokens prompt=%d completion=%d",
            result.prompt_tokens,
            result.completion_tokens,
        )
        return result

    async def close(self) -> None:
        await self._client.aclose()
