from __future__ import annotations

from pydantic import AnyUrl, Field

from kms_bot.schemas.common import StrictSchemaModel


class CleanedSection(StrictSchemaModel):
    heading: str
    content: str


class CleanedDocument(StrictSchemaModel):
    doc_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    sections: list[CleanedSection]
    plain_text: str = Field(min_length=1)


class ChunkRecord(StrictSchemaModel):
    chunk_id: str = Field(min_length=1)
    doc_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    section: str = Field(min_length=1)
    content: str = Field(min_length=1)
    url: AnyUrl
    tags: list[str]
    pipeline_version: int = Field(ge=1)