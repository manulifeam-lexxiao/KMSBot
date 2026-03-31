from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from kms_bot.api.router import api_router
from kms_bot.core.container import build_service_container
from kms_bot.core.errors import register_exception_handlers
from kms_bot.core.logging import configure_logging, register_request_logging
from kms_bot.core.settings import ApplicationSettings, load_settings


def create_app(settings: ApplicationSettings | None = None) -> FastAPI:
    app_settings = settings or load_settings()
    configure_logging(app_settings.logging)
    logger = logging.getLogger("kms_bot.app")

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        container = build_service_container(app_settings)
        container.database.initialize()
        application.state.container = container
        logger.info(
            "application_started",
            extra={
                "config_file": str(app_settings.config_file_path),
                "database_url": app_settings.database.url,
                "pipeline_version": app_settings.app.pipeline_version,
            },
        )
        try:
            yield
        finally:
            container.close()
            logger.info("application_stopped")

    app = FastAPI(
        title="KMS Bot Backend",
        version=app_settings.app.version,
        debug=app_settings.app.debug,
        lifespan=lifespan,
    )
    app.state.settings = app_settings

    register_request_logging(app)
    register_exception_handlers(app)
    app.include_router(api_router, prefix=app_settings.server.api_prefix)
    return app
