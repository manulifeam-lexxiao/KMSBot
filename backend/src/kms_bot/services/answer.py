"""Answer generator service.

Loads a prompt template from disk, renders it with the assembled
context and user query, sends the prompt to Azure OpenAI, and returns
the LLM answer string.

Fallback behaviour
------------------
* If ``context_text`` is empty (no chunks selected), the service
  returns ``NOT_FOUND_ANSWER`` immediately **without** calling the LLM.
* If the LLM returns an empty or whitespace-only response, the service
  returns ``NOT_FOUND_ANSWER``.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

from kms_bot.core.settings import ApplicationSettings
from kms_bot.schemas.query import AnswerGeneratorInput
from kms_bot.services.interfaces import AnswerService
from kms_bot.services.openai_client import AzureOpenAIClient, ChatMessage
from kms_bot.services.github_models_client import GithubModelsClient

logger = logging.getLogger(__name__)

NOT_FOUND_ANSWER = "Not found in the knowledge base."


@lru_cache(maxsize=16)
def _load_prompt_template(absolute_path: str) -> str:
    """Read a prompt `.md` file from disk and cache it."""
    path = Path(absolute_path)
    if not path.is_file():
        raise FileNotFoundError(f"Prompt template not found: {absolute_path}")
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"Prompt template is empty: {absolute_path}")
    logger.debug("Loaded prompt template: %s (%d chars)", absolute_path, len(text))
    return text


def render_prompt(template: str, *, context: str, query: str) -> str:
    """Substitute ``{context}`` and ``{query}`` placeholders."""
    return template.replace("{context}", context).replace("{query}", query)


class AzureOpenAIAnswerService(AnswerService):
    """Production implementation of :class:`AnswerService`.

    Loads prompt templates from the file system, renders them with
    the retrieval context, and delegates to a :class:`AzureOpenAIClient`.
    """

    def __init__(
        self,
        *,
        settings: ApplicationSettings,
        openai_client: AzureOpenAIClient,
    ) -> None:
        self._settings = settings
        self._client = openai_client

    async def generate_answer(self, payload: AnswerGeneratorInput) -> str:
        # ---- fast-path: no context ----
        if not payload.context_text.strip():
            logger.info("No context provided – returning fallback answer")
            return NOT_FOUND_ANSWER

        # ---- load and render prompt ----
        abs_path = str(self._settings.resolve_path(payload.prompt_template_path))
        template = _load_prompt_template(abs_path)
        system_prompt = render_prompt(
            template,
            context=payload.context_text,
            query=payload.query,
        )

        messages = [ChatMessage(role="system", content=system_prompt)]

        logger.debug(
            "Calling Azure OpenAI – query=%r  chunks=%d  prompt_len=%d",
            payload.query,
            len(payload.selected_chunks),
            len(system_prompt),
        )

        # ---- call LLM ----
        result = await self._client.chat(messages)
        answer = result.content.strip()

        if not answer:
            logger.warning("LLM returned empty answer – using fallback")
            return NOT_FOUND_ANSWER

        logger.info(
            "Answer generated – length=%d  tokens=%d/%d",
            len(answer),
            result.prompt_tokens,
            result.completion_tokens,
        )
        return answer


class GithubModelsAnswerService(AnswerService):
    """AnswerService backed by the GitHub Models inference API."""

    def __init__(
        self,
        *,
        settings: ApplicationSettings,
        github_client: GithubModelsClient,
    ) -> None:
        self._settings = settings
        self._client = github_client

    async def generate_answer(self, payload: AnswerGeneratorInput) -> str:
        if not payload.context_text.strip():
            logger.info("No context provided – returning fallback answer")
            return NOT_FOUND_ANSWER

        abs_path = str(self._settings.resolve_path(payload.prompt_template_path))
        template = _load_prompt_template(abs_path)
        system_prompt = render_prompt(
            template,
            context=payload.context_text,
            query=payload.query,
        )

        messages = [ChatMessage(role="system", content=system_prompt)]

        logger.debug(
            "Calling GitHub Models – query=%r  chunks=%d  prompt_len=%d",
            payload.query,
            len(payload.selected_chunks),
            len(system_prompt),
        )

        result = await self._client.chat(messages)
        answer = result.content.strip()

        if not answer:
            logger.warning("LLM returned empty answer – using fallback")
            return NOT_FOUND_ANSWER

        logger.info(
            "Answer generated – length=%d  tokens=%d/%d",
            len(answer),
            result.prompt_tokens,
            result.completion_tokens,
        )
        return answer
