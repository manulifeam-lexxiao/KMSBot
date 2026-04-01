from __future__ import annotations

from pydantic import Field

from kms_bot.schemas.common import StrictSchemaModel


class DocumentRegistryRecord(StrictSchemaModel):
    page_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    source_version: int
    last_updated: str = Field(min_length=1)
    raw_hash: str = Field(min_length=1)
    chunk_count: int = Field(ge=0)
    pipeline_version: int = Field(ge=1)
    index_status: str = Field(min_length=1)
    last_sync_time: str | None = None
    last_index_time: str | None = None
    error_message: str | None = None
    labels: str = "[]"
