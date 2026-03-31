from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from time import perf_counter
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request

from kms_bot.core.settings import LoggingSettings

STANDARD_LOG_RECORD_FIELDS = set(logging.makeLogRecord({}).__dict__.keys())


def _extract_extra_fields(record: logging.LogRecord) -> dict[str, Any]:
    return {
        key: value
        for key, value in record.__dict__.items()
        if key not in STANDARD_LOG_RECORD_FIELDS and not key.startswith("_")
    }


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        payload.update(_extract_extra_fields(record))
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True, default=str)


class KeyValueFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()
        base = f"{timestamp} {record.levelname} {record.name} {record.getMessage()}"
        extras = _extract_extra_fields(record)
        if extras:
            serialized = " ".join(
                f"{key}={json.dumps(value, ensure_ascii=True, default=str)}"
                for key, value in extras.items()
            )
            base = f"{base} {serialized}"
        if record.exc_info:
            base = f"{base}\n{self.formatException(record.exc_info)}"
        return base


def configure_logging(settings: LoggingSettings) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter() if settings.json_logs else KeyValueFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.level.upper())

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = True


def register_request_logging(app: FastAPI) -> None:
    logger = logging.getLogger("kms_bot.http")

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", uuid4().hex)
        request.state.request_id = request_id
        started = perf_counter()

        response = await call_next(request)

        duration_ms = round((perf_counter() - started) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
