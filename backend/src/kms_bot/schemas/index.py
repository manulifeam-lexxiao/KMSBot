from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from kms_bot.schemas.common import StrictSchemaModel


class IndexStatusResponse(StrictSchemaModel):
    status: Literal["idle", "running", "success", "error"]
    current_job_id: str | None = None
    pipeline_version: int = Field(ge=1)
    last_started_at: datetime | None = None
    last_finished_at: datetime | None = None
    last_success_at: datetime | None = None
    indexed_documents: int = Field(ge=0)
    indexed_chunks: int = Field(ge=0)
    error_message: str | None = None
