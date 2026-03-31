from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from kms_bot.schemas.common import StrictSchemaModel


class SyncStatusResponse(StrictSchemaModel):
    status: Literal["idle", "running", "success", "error"]
    mode: Literal["none", "full", "incremental"]
    current_job_id: str | None = None
    pipeline_version: int = Field(ge=1)
    last_started_at: datetime | None = None
    last_finished_at: datetime | None = None
    last_success_at: datetime | None = None
    processed_pages: int = Field(ge=0)
    changed_pages: int = Field(ge=0)
    error_message: str | None = None