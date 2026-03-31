"""Unit tests for the HTML cleaner module."""

from __future__ import annotations

import pytest

from kms_bot.services.html_cleaner import (
    DEFAULT_SECTION_HEADING,
    Section,
    clean_html,
)


# ── heading extraction ────────────────────────────────────────


class TestHeadingExtraction:
    def test_single_heading_with_paragraph(self) -> None:
        html = "<h2>Overview</h2><p>Some content here.</p>"
        sections, _ = clean_html(html)
        assert len(sections) == 1
        assert sections[0].heading == "Overview"
        assert sections[0].content == "Some content here."

    def test_multiple_headings(self) -> None:
        html = (
            "<h2>First</h2><p>A</p>"
            "<h2>Second</h2><p>B</p>"
            "<h3>Third</h3><p>C</p>"
        )
        sections, _ = clean_html(html)
        assert len(sections) == 3
        assert [s.heading for s in sections] == ["First", "Second", "Third"]

    def test_content_before_any_heading(self) -> None:
        html = "<p>Intro text</p><h2>Details</h2><p>More text</p>"
        sections, _ = clean_html(html)
        assert len(sections) == 2
        assert sections[0].heading == DEFAULT_SECTION_HEADING
        assert sections[0].content == "Intro text"
        assert sections[1].heading == "Details"

    def test_heading_inside_div(self) -> None:
        html = "<div><h2>Nested Heading</h2><p>Content</p></div>"
        sections, _ = clean_html(html)
        assert any(s.heading == "Nested Heading" for s in sections)


# ── paragraph extraction ──────────────────────────────────────


class TestParagraphExtraction:
    def test_simple_paragraphs(self) -> None:
        html = "<h2>Section</h2><p>First paragraph.</p><p>Second paragraph.</p>"
        sections, _ = clean_html(html)
        assert "First paragraph." in sections[0].content
        assert "Second paragraph." in sections[0].content

    def test_whitespace_normalisation(self) -> None:
        html = "<h2>S</h2><p>  lots   of   spaces  </p>"
        sections, _ = clean_html(html)
        assert "lots of spaces" in sections[0].content


# ── list handling ─────────────────────────────────────────────


class TestListHandling:
    def test_unordered_list(self) -> None:
        html = "<h2>Items</h2><ul><li>Apple</li><li>Banana</li></ul>"
        sections, _ = clean_html(html)
        assert "• Apple" in sections[0].content
        assert "• Banana" in sections[0].content

    def test_ordered_list(self) -> None:
        html = "<h2>Steps</h2><ol><li>First</li><li>Second</li><li>Third</li></ol>"
        sections, _ = clean_html(html)
        assert "1. First" in sections[0].content
        assert "2. Second" in sections[0].content
        assert "3. Third" in sections[0].content


# ── table handling ────────────────────────────────────────────


class TestTableHandling:
    def test_simple_table(self) -> None:
        html = (
            "<h2>Data</h2>"
            "<table>"
            "<tr><th>Name</th><th>Value</th></tr>"
            "<tr><td>A</td><td>1</td></tr>"
            "<tr><td>B</td><td>2</td></tr>"
            "</table>"
        )
        sections, _ = clean_html(html)
        assert "Name | Value" in sections[0].content
        assert "A | 1" in sections[0].content
        assert "B | 2" in sections[0].content


# ── code block handling ──────────────────────────────────────


class TestCodeBlock:
    def test_pre_tag(self) -> None:
        html = "<h2>Code</h2><pre><code>print('hello')</code></pre>"
        sections, _ = clean_html(html)
        assert "print('hello')" in sections[0].content

    def test_confluence_code_macro(self) -> None:
        html = (
            '<h2>Code</h2>'
            '<ac:structured-macro ac:name="code">'
            '<ac:parameter ac:name="language">python</ac:parameter>'
            "<ac:plain-text-body>def foo(): pass</ac:plain-text-body>"
            "</ac:structured-macro>"
        )
        sections, _ = clean_html(html)
        assert "def foo(): pass" in sections[0].content


# ── noise removal ─────────────────────────────────────────────


class TestNoiseRemoval:
    def test_script_and_style_removed(self) -> None:
        html = (
            "<h2>Real</h2><p>Content</p>"
            "<script>alert(1)</script>"
            "<style>.x{color:red}</style>"
        )
        sections, plain_text = clean_html(html)
        assert "alert" not in plain_text
        assert "color:red" not in plain_text

    def test_toc_macro_removed(self) -> None:
        html = (
            '<ac:structured-macro ac:name="toc"></ac:structured-macro>'
            "<h2>Title</h2><p>Text</p>"
        )
        sections, plain_text = clean_html(html)
        assert "toc" not in plain_text.lower()

    def test_info_macro_content_kept(self) -> None:
        html = (
            "<h2>Info</h2>"
            '<ac:structured-macro ac:name="info">'
            "<ac:rich-text-body><p>Important note here.</p></ac:rich-text-body>"
            "</ac:structured-macro>"
        )
        sections, plain_text = clean_html(html)
        assert "Important note here." in plain_text


# ── plain_text generation ─────────────────────────────────────


class TestPlainText:
    def test_plain_text_contains_all_sections(self) -> None:
        html = "<h2>A</h2><p>Alpha</p><h2>B</h2><p>Beta</p>"
        sections, plain_text = clean_html(html)
        assert "A\nAlpha" in plain_text
        assert "B\nBeta" in plain_text

    def test_empty_html_returns_empty(self) -> None:
        sections, plain_text = clean_html("")
        assert sections == []
        assert plain_text == ""

    def test_whitespace_only_html(self) -> None:
        sections, plain_text = clean_html("   \n\t  ")
        assert sections == []
        assert plain_text == ""


# ── edge cases ────────────────────────────────────────────────


class TestEdgeCases:
    def test_heading_only_no_body(self) -> None:
        html = "<h2>Lonely Heading</h2>"
        sections, _ = clean_html(html)
        assert sections == []

    def test_nested_lists(self) -> None:
        html = (
            "<h2>List</h2>"
            "<ul><li>A<ul><li>A1</li></ul></li><li>B</li></ul>"
        )
        sections, _ = clean_html(html)
        # Nested li text should be captured in parent li
        assert "A" in sections[0].content
        assert "B" in sections[0].content

    def test_mixed_content(self) -> None:
        html = (
            "<h2>Mixed</h2>"
            "<p>Paragraph</p>"
            "<ul><li>Item</li></ul>"
            "<table><tr><td>Cell</td></tr></table>"
            "<pre>code</pre>"
        )
        sections, _ = clean_html(html)
        content = sections[0].content
        assert "Paragraph" in content
        assert "• Item" in content
        assert "Cell" in content
        assert "code" in content
