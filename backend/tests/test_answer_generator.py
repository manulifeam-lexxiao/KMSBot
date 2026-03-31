"""Unit tests for the answer generator module.

All tests use mocked inputs — no live Azure OpenAI endpoints required.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from kms_bot.core.settings import ApplicationSettings
from kms_bot.schemas.query import AnswerGeneratorInput, SearchResultHit
from kms_bot.services.answer import (
    NOT_FOUND_ANSWER,
    AzureOpenAIAnswerService,
    _load_prompt_template,
    render_prompt,
)
from kms_bot.services.openai_client import AzureOpenAIClient, ChatCompletionResult, ChatMessage


# ── helpers ───────────────────────────────────────────────────


def _hit(
    chunk_id: str = "1#overview#1",
    doc_id: str = "1",
    title: str = "Reset iPension Access",
    section: str = "Overview",
    content: str = "To reset iPension access, contact the helpdesk.",
    url: str = "https://example.com/1",
    score: float = 0.9,
    tags: list[str] | None = None,
    pipeline_version: int = 1,
) -> SearchResultHit:
    return SearchResultHit(
        chunk_id=chunk_id,
        doc_id=doc_id,
        title=title,
        section=section,
        content=content,
        url=url,
        score=score,
        tags=tags or [],
        pipeline_version=pipeline_version,
    )


def _make_payload(
    *,
    query: str = "How do I reset iPension access?",
    normalized_query: str = "how do i reset ipension access",
    context_text: str = "--- Chunk 1 ---\nDocument: Reset iPension Access\nSection: Overview\n\nTo reset, contact helpdesk.",
    selected_chunks: list[SearchResultHit] | None = None,
    include_debug: bool = False,
    prompt_template_path: str = "prompts/query_answering/default.md",
) -> AnswerGeneratorInput:
    return AnswerGeneratorInput(
        query=query,
        normalized_query=normalized_query,
        context_text=context_text,
        selected_chunks=selected_chunks or [_hit()],
        include_debug=include_debug,
        prompt_template_path=prompt_template_path,
    )


def _completion(content: str = "Contact the helpdesk to reset iPension access.") -> ChatCompletionResult:
    return ChatCompletionResult(
        content=content,
        model="gpt-4o",
        prompt_tokens=100,
        completion_tokens=20,
    )


@pytest.fixture()
def settings(tmp_path: Path) -> ApplicationSettings:
    # Write a prompt template to a temp directory
    prompt_dir = tmp_path / "prompts" / "query_answering"
    prompt_dir.mkdir(parents=True)
    (prompt_dir / "default.md").write_text(
        "System prompt.\n\n## Context\n\n{context}\n\n## Question\n\n{query}",
        encoding="utf-8",
    )
    s = ApplicationSettings(
        app={"pipeline_version": 1},
        answer={"endpoint": "https://test.openai.azure.com", "api_key": "fake", "chat_deployment": "gpt-4o"},
    )
    s.bind_runtime_paths(repo_root=tmp_path, config_file_path=tmp_path / "config" / "app.example.yaml")
    return s


@pytest.fixture()
def mock_openai_client() -> AsyncMock:
    client = AsyncMock(spec=AzureOpenAIClient)
    client.chat.return_value = _completion()
    return client


@pytest.fixture()
def service(settings: ApplicationSettings, mock_openai_client: AsyncMock) -> AzureOpenAIAnswerService:
    return AzureOpenAIAnswerService(settings=settings, openai_client=mock_openai_client)


# ── render_prompt ─────────────────────────────────────────────


class TestRenderPrompt:
    def test_substitutes_placeholders(self) -> None:
        template = "Context: {context}\nQuestion: {query}"
        result = render_prompt(template, context="Some context", query="What?")
        assert result == "Context: Some context\nQuestion: What?"

    def test_no_placeholders_passthrough(self) -> None:
        template = "No placeholders here"
        result = render_prompt(template, context="ctx", query="q")
        assert result == "No placeholders here"


# ── _load_prompt_template ─────────────────────────────────────


class TestLoadPromptTemplate:
    def test_loads_existing_file(self, tmp_path: Path) -> None:
        f = tmp_path / "test.md"
        f.write_text("Hello template", encoding="utf-8")
        _load_prompt_template.cache_clear()
        result = _load_prompt_template(str(f))
        assert result == "Hello template"

    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        _load_prompt_template.cache_clear()
        with pytest.raises(FileNotFoundError):
            _load_prompt_template(str(tmp_path / "nope.md"))

    def test_raises_on_empty_file(self, tmp_path: Path) -> None:
        f = tmp_path / "empty.md"
        f.write_text("", encoding="utf-8")
        _load_prompt_template.cache_clear()
        with pytest.raises(ValueError, match="empty"):
            _load_prompt_template(str(f))


# ── AzureOpenAIAnswerService ─────────────────────────────────


class TestAzureOpenAIAnswerService:
    @pytest.mark.asyncio
    async def test_generates_answer(self, service: AzureOpenAIAnswerService, mock_openai_client: AsyncMock) -> None:
        _load_prompt_template.cache_clear()
        payload = _make_payload()
        answer = await service.generate_answer(payload)
        assert answer == "Contact the helpdesk to reset iPension access."
        mock_openai_client.chat.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_fallback_on_empty_context(self, service: AzureOpenAIAnswerService, mock_openai_client: AsyncMock) -> None:
        payload = _make_payload(context_text="", selected_chunks=[])
        answer = await service.generate_answer(payload)
        assert answer == NOT_FOUND_ANSWER
        mock_openai_client.chat.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_fallback_on_whitespace_context(self, service: AzureOpenAIAnswerService, mock_openai_client: AsyncMock) -> None:
        payload = _make_payload(context_text="   \n  ", selected_chunks=[])
        answer = await service.generate_answer(payload)
        assert answer == NOT_FOUND_ANSWER
        mock_openai_client.chat.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_fallback_on_empty_llm_response(self, service: AzureOpenAIAnswerService, mock_openai_client: AsyncMock) -> None:
        _load_prompt_template.cache_clear()
        mock_openai_client.chat.return_value = _completion(content="   ")
        payload = _make_payload()
        answer = await service.generate_answer(payload)
        assert answer == NOT_FOUND_ANSWER

    @pytest.mark.asyncio
    async def test_prompt_template_passed_as_system_message(self, service: AzureOpenAIAnswerService, mock_openai_client: AsyncMock) -> None:
        _load_prompt_template.cache_clear()
        payload = _make_payload()
        await service.generate_answer(payload)

        call_args = mock_openai_client.chat.call_args
        messages = call_args[0][0]
        assert len(messages) == 1
        assert messages[0].role == "system"
        assert payload.query in messages[0].content
        assert "Chunk 1" in messages[0].content

    @pytest.mark.asyncio
    async def test_missing_template_raises(self, settings: ApplicationSettings, mock_openai_client: AsyncMock) -> None:
        _load_prompt_template.cache_clear()
        svc = AzureOpenAIAnswerService(settings=settings, openai_client=mock_openai_client)
        payload = _make_payload(prompt_template_path="prompts/nonexistent/missing.md")
        with pytest.raises(FileNotFoundError):
            await svc.generate_answer(payload)
