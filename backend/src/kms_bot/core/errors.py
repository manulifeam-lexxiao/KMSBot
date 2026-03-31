from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from kms_bot.schemas.common import ErrorResponse


class AppError(Exception):
    def __init__(
        self,
        *,
        error_code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class ModuleNotReadyError(AppError):
    def __init__(self, module_name: str) -> None:
        super().__init__(
            error_code="module_not_ready",
            message=f"{module_name} module is not implemented yet.",
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            details={"module": module_name},
        )


def _request_id_from(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _response_payload(
    *,
    error_code: str,
    message: str,
    request_id: str | None,
    details: dict[str, Any] | None = None,
) -> ErrorResponse:
    payload_details = dict(details or {})
    if request_id is not None:
        payload_details.setdefault("request_id", request_id)
    return ErrorResponse(
        error_code=error_code,
        message=message,
        details=payload_details or None,
    )


def register_exception_handlers(app: FastAPI) -> None:
    logger = logging.getLogger("kms_bot.errors")

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        request_id = _request_id_from(request)
        logger.warning(
            "application_error",
            extra={
                "request_id": request_id,
                "error_code": exc.error_code,
                "status_code": exc.status_code,
                "path": request.url.path,
            },
        )
        payload = _response_payload(
            error_code=exc.error_code,
            message=exc.message,
            request_id=request_id,
            details=exc.details,
        )
        return JSONResponse(
            status_code=exc.status_code, content=payload.model_dump(exclude_none=True)
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        request_id = _request_id_from(request)
        logger.warning(
            "request_validation_error",
            extra={"request_id": request_id, "path": request.url.path},
        )
        payload = _response_payload(
            error_code="invalid_request",
            message="Request validation failed.",
            request_id=request_id,
            details={"errors": exc.errors()},
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=payload.model_dump(exclude_none=True),
        )

    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        request_id = _request_id_from(request)
        detail = exc.detail if isinstance(exc.detail, str) else "Request failed."
        logger.warning(
            "http_exception",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "status_code": exc.status_code,
            },
        )
        payload = _response_payload(
            error_code="http_error",
            message=detail,
            request_id=request_id,
        )
        return JSONResponse(
            status_code=exc.status_code, content=payload.model_dump(exclude_none=True)
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
        request_id = _request_id_from(request)
        logger.exception(
            "unexpected_exception",
            extra={"request_id": request_id, "path": request.url.path},
        )
        payload = _response_payload(
            error_code="internal_server_error",
            message="An unexpected server error occurred.",
            request_id=request_id,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=payload.model_dump(exclude_none=True),
        )
