from __future__ import annotations

from datetime import datetime
from typing import Literal

from kms_bot.schemas.common import StrictSchemaModel

DependencyStatus = Literal["ok", "degraded", "error", "not_configured"]
HealthStatus = Literal["ok", "degraded", "error"]


class HealthDependencies(StrictSchemaModel):
    sqlite: DependencyStatus
    azure_ai_search: DependencyStatus
    azure_openai: DependencyStatus


class HealthResponse(StrictSchemaModel):
    status: HealthStatus
    service: Literal["kms-bot-backend"]
    version: str
    timestamp: datetime
    dependencies: HealthDependencies
