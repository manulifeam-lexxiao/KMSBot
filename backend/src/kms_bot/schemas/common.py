from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictSchemaModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ErrorResponse(StrictSchemaModel):
    error_code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    details: dict[str, Any] | None = None


JobType = Literal["full_sync", "incremental_sync", "index_rebuild"]


class OperationAcceptedResponse(StrictSchemaModel):
    job_id: str = Field(min_length=1)
    job_type: JobType
    status: Literal["accepted"]
    requested_at: datetime
    pipeline_version: int = Field(ge=1)
    message: str = Field(min_length=1)
