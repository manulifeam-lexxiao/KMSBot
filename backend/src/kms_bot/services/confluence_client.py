from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from kms_bot.core.settings import ConfluenceSettings

logger = logging.getLogger(__name__)

_EXPAND = "version,body.storage,metadata.labels,_links"


@dataclass(slots=True)
class ConfluencePage:
    """Lightweight data holder for a fetched Confluence page."""

    page_id: str
    title: str
    source_version: int
    last_updated: str
    body_html: str
    url: str
    labels: list[str]


class ConfluenceClient:
    """Async wrapper over the Confluence Cloud REST API v1."""

    def __init__(self, settings: ConfluenceSettings) -> None:
        self._settings = settings
        self._base_api = f"{settings.base_url.rstrip('/')}/rest/api"

    @property
    def is_configured(self) -> bool:
        return bool(
            self._settings.base_url
            and self._settings.space_key
            and self._settings.username
            and self._settings.api_token
        )

    def _build_auth(self) -> httpx.BasicAuth:
        return httpx.BasicAuth(self._settings.username, self._settings.api_token)

    def _page_url(self, result: dict[str, Any]) -> str:
        webui = result.get("_links", {}).get("webui", "")
        base = self._settings.base_url.rstrip("/")
        return f"{base}{webui}" if webui else base

    def _parse_page(self, result: dict[str, Any]) -> ConfluencePage:
        version_info = result.get("version", {})
        label_results = result.get("metadata", {}).get("labels", {}).get("results", [])
        labels = [lbl["name"] for lbl in label_results if isinstance(lbl, dict) and "name" in lbl]
        return ConfluencePage(
            page_id=str(result["id"]),
            title=result["title"],
            source_version=int(version_info.get("number", 1)),
            last_updated=version_info.get("when", ""),
            body_html=result.get("body", {}).get("storage", {}).get("value", ""),
            url=self._page_url(result),
            labels=labels,
        )

    async def fetch_all_pages(self) -> list[ConfluencePage]:
        """Fetch all pages (with body) from the configured space, handling pagination."""
        pages: list[ConfluencePage] = []
        start = 0
        limit = self._settings.page_limit

        async with httpx.AsyncClient(auth=self._build_auth(), timeout=60.0) as client:
            while True:
                params = {
                    "spaceKey": self._settings.space_key,
                    "type": "page",
                    "expand": _EXPAND,
                    "limit": str(limit),
                    "start": str(start),
                }
                logger.debug("confluence_fetch_pages", extra={"start": start, "limit": limit})
                resp = await client.get(f"{self._base_api}/content", params=params)
                resp.raise_for_status()
                data = resp.json()

                for result in data.get("results", []):
                    pages.append(self._parse_page(result))

                if data.get("_links", {}).get("next"):
                    start += limit
                else:
                    break

        logger.info("confluence_fetched_all_pages", extra={"count": len(pages)})
        return pages

    async def fetch_pages_updated_since(self, since_iso: str) -> list[ConfluencePage]:
        """Fetch pages modified after *since_iso* using CQL search."""
        pages: list[ConfluencePage] = []
        start = 0
        limit = self._settings.page_limit
        cql = f'space="{self._settings.space_key}" and type=page and lastModified>="{since_iso}"'

        async with httpx.AsyncClient(auth=self._build_auth(), timeout=60.0) as client:
            while True:
                params = {
                    "cql": cql,
                    "expand": _EXPAND,
                    "limit": str(limit),
                    "start": str(start),
                }
                logger.debug(
                    "confluence_fetch_incremental", extra={"start": start, "since": since_iso}
                )
                resp = await client.get(f"{self._base_api}/content/search", params=params)
                resp.raise_for_status()
                data = resp.json()

                for result in data.get("results", []):
                    pages.append(self._parse_page(result))

                if data.get("_links", {}).get("next"):
                    start += limit
                else:
                    break

        logger.info(
            "confluence_fetched_incremental", extra={"count": len(pages), "since": since_iso}
        )
        return pages
