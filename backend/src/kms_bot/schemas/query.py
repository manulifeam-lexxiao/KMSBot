from __future__ import annotations

from pydantic import AnyUrl, Field

from kms_bot.schemas.common import StrictSchemaModel
from kms_bot.schemas.documents import ChunkRecord


class QueryRequest(StrictSchemaModel):
    query: str = Field(min_length=1)
    top_k: int = Field(ge=1, le=10)
    include_debug: bool


class SearchResultHit(ChunkRecord):
    score: float


class QuerySource(StrictSchemaModel):
    title: str = Field(min_length=1)
    url: AnyUrl
    section: str = Field(min_length=1)
    doc_id: str = Field(min_length=1)
    chunk_id: str = Field(min_length=1)


class RelatedDocument(StrictSchemaModel):
    page_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    url: AnyUrl


class QueryDebugInfo(StrictSchemaModel):
    normalized_query: str
    selected_chunks: list[SearchResultHit]


class QueryResponse(StrictSchemaModel):
    answer: str
    sources: list[QuerySource]
    related_documents: list[RelatedDocument]
    debug: QueryDebugInfo


class AnswerGeneratorInput(StrictSchemaModel):
    query: str = Field(min_length=1)
    normalized_query: str = Field(min_length=1)
    prompt_template_path: str = Field(pattern=r"^prompts/.+\.md$")
    selected_chunks: list[SearchResultHit]
    context_text: str = ""
    include_debug: bool
