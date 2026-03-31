"""Deterministic, rule-based HTML → structured-text cleaner for Confluence storage format."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from bs4 import BeautifulSoup, NavigableString, Tag

logger = logging.getLogger(__name__)

HEADING_TAGS = frozenset({"h1", "h2", "h3", "h4", "h5", "h6"})
NOISE_TAGS = frozenset({"script", "style", "nav", "iframe", "object", "embed", "noscript"})
NOISE_MACRO_NAMES = frozenset({"toc", "status", "excerpt-include", "recently-updated", "children"})
CONTENT_MACRO_NAMES = frozenset({"info", "note", "warning", "tip", "expand"})

DEFAULT_SECTION_HEADING = "Introduction"


@dataclass(slots=True)
class Section:
    heading: str
    content: str


# ── public API ────────────────────────────────────────────────


def clean_html(raw_html: str) -> tuple[list[Section], str]:
    """Parse raw Confluence HTML/XHTML and return (sections, plain_text).

    The function is intentionally pure – no I/O, no side effects.
    """
    soup = BeautifulSoup(raw_html, "html.parser")
    _remove_noise(soup)
    _unwrap_content_macros(soup)

    blocks: list[tuple[str, str]] = []
    body = soup.body if soup.body else soup
    _collect_blocks(body, blocks)

    sections = _group_into_sections(blocks)
    plain_text = _build_plain_text(sections)
    return sections, plain_text


# ── noise removal ─────────────────────────────────────────────


def _remove_noise(soup: BeautifulSoup) -> None:
    """Remove low-value elements from the parsed tree."""
    for tag_name in NOISE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Remove Confluence structured macros that are noise
    for macro in soup.find_all("ac:structured-macro"):
        macro_name = (macro.get("ac:name") or "").lower()
        if macro_name in NOISE_MACRO_NAMES:
            macro.decompose()


def _unwrap_content_macros(soup: BeautifulSoup) -> None:
    """Unwrap INFO/NOTE/WARNING macros to expose their rich-text body as inline content."""
    for macro in soup.find_all("ac:structured-macro"):
        macro_name = (macro.get("ac:name") or "").lower()
        if macro_name in CONTENT_MACRO_NAMES:
            rich_body = macro.find("ac:rich-text-body")
            if rich_body:
                macro.replace_with(rich_body)
                rich_body.unwrap()
            else:
                macro.decompose()

    # Unwrap any remaining ac:rich-text-body wrappers
    for rtb in soup.find_all("ac:rich-text-body"):
        rtb.unwrap()


# ── block collection ──────────────────────────────────────────


def _collect_blocks(element: Tag, blocks: list[tuple[str, str]]) -> None:
    """Walk the element tree and produce a flat list of (type, text) blocks.

    Headings yield ("heading", text), everything else yields ("content", text).
    Divs are recursed into so that headings nested inside divs are still detected.
    """
    for child in element.children:
        if isinstance(child, NavigableString):
            text = child.strip()
            if text:
                blocks.append(("content", text))
            continue

        if not isinstance(child, Tag):
            continue

        if child.name in HEADING_TAGS:
            blocks.append(("heading", _get_text(child)))
        elif child.name in {"div", "section", "article", "main"}:
            _collect_blocks(child, blocks)
        elif child.name in {"ul"}:
            rendered = _render_unordered_list(child)
            if rendered:
                blocks.append(("content", rendered))
        elif child.name in {"ol"}:
            rendered = _render_ordered_list(child)
            if rendered:
                blocks.append(("content", rendered))
        elif child.name in {"table"}:
            rendered = _render_table(child)
            if rendered:
                blocks.append(("content", rendered))
        elif child.name in {"pre"}:
            rendered = _render_code_block(child)
            if rendered:
                blocks.append(("content", rendered))
        elif _is_confluence_code_macro(child):
            rendered = _render_confluence_code_macro(child)
            if rendered:
                blocks.append(("content", rendered))
        else:
            text = _get_text(child)
            if text:
                blocks.append(("content", text))


# ── section grouping ──────────────────────────────────────────


def _group_into_sections(blocks: list[tuple[str, str]]) -> list[Section]:
    """Group (type, text) blocks into sections delimited by headings."""
    sections: list[Section] = []
    current_heading = DEFAULT_SECTION_HEADING
    current_parts: list[str] = []

    for block_type, text in blocks:
        if block_type == "heading":
            _flush_section(sections, current_heading, current_parts)
            current_heading = text.strip() or DEFAULT_SECTION_HEADING
            current_parts = []
        else:
            stripped = text.strip()
            if stripped:
                current_parts.append(stripped)

    _flush_section(sections, current_heading, current_parts)
    return sections


def _flush_section(sections: list[Section], heading: str, parts: list[str]) -> None:
    if not parts:
        return
    content = "\n\n".join(parts)
    if content.strip():
        sections.append(Section(heading=heading, content=content.strip()))


# ── element renderers ─────────────────────────────────────────


def _render_unordered_list(element: Tag) -> str:
    items: list[str] = []
    for li in element.find_all("li", recursive=False):
        text = _get_text(li)
        if text:
            items.append(f"• {text}")
    return "\n".join(items)


def _render_ordered_list(element: Tag) -> str:
    items: list[str] = []
    for idx, li in enumerate(element.find_all("li", recursive=False), 1):
        text = _get_text(li)
        if text:
            items.append(f"{idx}. {text}")
    return "\n".join(items)


def _render_table(element: Tag) -> str:
    rows: list[str] = []
    for tr in element.find_all("tr"):
        cells: list[str] = []
        for cell in tr.find_all(["th", "td"]):
            cells.append(_get_text(cell))
        if cells:
            rows.append(" | ".join(cells))
    return "\n".join(rows)


def _render_code_block(element: Tag) -> str:
    """Render <pre> (optionally containing <code>) as plain text."""
    return element.get_text()


def _is_confluence_code_macro(element: Tag) -> bool:
    return (
        element.name == "ac:structured-macro" and (element.get("ac:name") or "").lower() == "code"
    )


def _render_confluence_code_macro(element: Tag) -> str:
    plain_body = element.find("ac:plain-text-body")
    if plain_body:
        return plain_body.get_text()
    return _get_text(element)


# ── helpers ───────────────────────────────────────────────────


def _get_text(element: Tag) -> str:
    """Extract text from an element, collapsing runs of whitespace."""
    raw = element.get_text(separator=" ")
    return re.sub(r"\s+", " ", raw).strip()


def _build_plain_text(sections: list[Section]) -> str:
    parts: list[str] = []
    for section in sections:
        parts.append(f"{section.heading}\n{section.content}")
    return "\n\n".join(parts)
