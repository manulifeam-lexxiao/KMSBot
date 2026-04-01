"""AI 查询规划服务 —— 分析用户问题并生成结构化搜索方案。"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from kms_bot.core.settings import ApplicationSettings
from kms_bot.core.utils import utcnow
from kms_bot.repositories.document_registry import DocumentRegistryRepository
from kms_bot.repositories.token_usage import TokenUsageRepository
from kms_bot.services.interfaces import AnswerService
from kms_bot.services.openai_client import ChatMessage

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class QueryPlan:
    """AI 分析后的结构化查询计划。"""

    intent: str
    search_keywords: list[str]
    label_filters: list[str]
    synonym_expansions: list[str]
    reasoning: str

    @property
    def all_search_terms(self) -> list[str]:
        """合并 keywords + synonyms 去重后的搜索词列表。"""
        seen: set[str] = set()
        terms: list[str] = []
        for term in self.search_keywords + self.synonym_expansions:
            lower = term.lower()
            if lower not in seen:
                seen.add(lower)
                terms.append(term)
        return terms


@lru_cache(maxsize=4)
def _load_planning_prompt(absolute_path: str) -> str:
    path = Path(absolute_path)
    if not path.is_file():
        raise FileNotFoundError(f"Planning prompt not found: {absolute_path}")
    return path.read_text(encoding="utf-8").strip()


def _extract_json(text: str) -> dict:
    """从 LLM 响应中提取 JSON 对象（支持 markdown code blocks）。"""
    # 尝试匹配 ```json ... ``` 代码块
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    # 直接尝试解析
    return json.loads(text)


def _fallback_plan(query: str) -> QueryPlan:
    """AI 失败时的降级方案：简单关键词提取。"""
    words = re.findall(r"[a-zA-Z0-9]+", query.lower())
    keywords = [w for w in words if len(w) > 2][:5]
    return QueryPlan(
        intent="find",
        search_keywords=keywords,
        label_filters=[],
        synonym_expansions=[],
        reasoning="Fallback: simple keyword extraction",
    )


class QueryPlannerService:
    """调用 LLM 分析用户问题，输出结构化 QueryPlan。"""

    def __init__(
        self,
        *,
        settings: ApplicationSettings,
        answer_service: AnswerService,
        registry_repository: DocumentRegistryRepository,
        token_usage_repository: TokenUsageRepository | None = None,
    ) -> None:
        self._settings = settings
        self._answer_service = answer_service
        self._registry = registry_repository
        self._token_repo = token_usage_repository

    def _get_available_labels(self) -> list[str]:
        """从 document_registry 获取所有唯一的 labels。"""
        rows = self._registry.fetch_all(
            "SELECT DISTINCT labels FROM document_registry WHERE labels != '[]'"
        )
        all_labels: set[str] = set()
        for row in rows:
            try:
                labels = json.loads(row["labels"])
                all_labels.update(labels)
            except (json.JSONDecodeError, TypeError):
                continue
        return sorted(all_labels)

    async def plan(self, query: str, *, mode: str = "standard") -> QueryPlan:
        """分析用户问题并返回 QueryPlan。失败时降级为简单关键词提取。"""
        try:
            abs_path = str(self._settings.resolve_path(self._settings.prompts.query_planning))
            template = _load_planning_prompt(abs_path)

            available_labels = self._get_available_labels()
            labels_text = ", ".join(available_labels) if available_labels else "(no labels yet)"

            prompt = template.replace("{query}", query).replace("{available_labels}", labels_text)

            messages = [ChatMessage(role="system", content=prompt)]

            # 使用 answer_service 底层的 LLM 客户端
            from kms_bot.services.answer import AzureOpenAIAnswerService, GithubModelsAnswerService
            from kms_bot.services.answer_router import ProviderAnswerRouter

            service = self._answer_service
            if isinstance(service, ProviderAnswerRouter):
                service = service._current_service  # type: ignore[attr-defined]

            if isinstance(service, AzureOpenAIAnswerService):
                result = await service._client.chat(
                    messages, temperature=0.0, max_completion_tokens=512
                )
                provider = "azure_openai"
            elif isinstance(service, GithubModelsAnswerService):
                result = await service._client.chat(
                    messages, temperature=0.0, max_completion_tokens=512
                )
                provider = "github_models"
            else:
                logger.warning("Unsupported answer service for planning, using fallback")
                return _fallback_plan(query)

            # 记录 token 使用
            if self._token_repo:
                self._token_repo.record(
                    timestamp=utcnow().isoformat(),
                    query=query,
                    mode=mode,
                    provider=provider,
                    stage="planning",
                    prompt_tokens=result.prompt_tokens,
                    completion_tokens=result.completion_tokens,
                    model=result.model,
                )

            # 解析 JSON 响应
            plan_data = _extract_json(result.content)
            return QueryPlan(
                intent=plan_data.get("intent", "find"),
                search_keywords=plan_data.get("search_keywords", []),
                label_filters=plan_data.get("label_filters", []),
                synonym_expansions=plan_data.get("synonym_expansions", []),
                reasoning=plan_data.get("reasoning", ""),
            )

        except Exception as exc:
            logger.warning("Query planning failed, using fallback: %s", exc)
            return _fallback_plan(query)
