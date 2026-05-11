"""Tests for notion-to-md utilities."""

import pytest
from notion_to_md.utils import (
    add_tab_space,
    bold,
    bullet,
    code_block,
    divider,
    equation,
    heading1,
    heading2,
    heading3,
    image,
    inline_code,
    inline_equation,
    italic,
    link,
    quote,
    strikethrough,
    table,
    todo,
    toggle,
    underline,
)


class TestMarkdownUtils:
    def test_inline_code(self):
        assert inline_code("hello") == "`hello`"
        assert inline_code("") == "``"

    def test_inline_equation(self):
        assert inline_equation("x^2") == "$x^2$"

    def test_bold(self):
        assert bold("text") == "**text**"

    def test_italic(self):
        assert italic("text") == "_text_"

    def test_strikethrough(self):
        assert strikethrough("text") == "~~text~~"

    def test_underline(self):
        assert underline("text") == "<u>text</u>"

    def test_link(self):
        assert link("Google", "https://google.com") == "[Google](https://google.com)"

    def test_code_block(self):
        result = code_block("print('hello')", "python")
        assert "```python" in result
        assert "print('hello')" in result

        assert code_block("", "python") == ""

        result = code_block("code", "")
        assert "```plaintext" in result

    def test_equation(self):
        result = equation("x = 5")
        assert "$$" in result
        assert "x = 5" in result

    def test_heading1(self):
        assert heading1("Title") == "# Title"

    def test_heading2(self):
        assert heading2("Subtitle") == "## Subtitle"

    def test_heading3(self):
        assert heading3("Heading") == "### Heading"

    def test_quote(self):
        result = quote("text")
        assert result.startswith("> ")
        assert "text" in result

    def test_bullet(self):
        assert bullet("item") == "- item"
        assert bullet("item", 1) == "1. item"
        assert bullet("item", 5) == "5. item"

    def test_todo(self):
        assert todo("task", True) == "- [x] task"
        assert todo("task", False) == "- [ ] task"

    def test_divider(self):
        assert divider() == "---"

    def test_toggle(self):
        result = toggle("Title", "Content")
        assert "<details>" in result
        assert "<summary>Title</summary>" in result
        assert "Content" in result

        result = toggle()
        assert result == ""

        result = toggle(summary=None, children="Content")
        assert result == "Content"

    def test_table(self):
        cells = [["Name", "Age"], ["Alice", "30"], ["Bob", "25"]]
        result = table(cells)
        assert "|" in result
        assert "Name" in result
        assert "Age" in result
        assert "Alice" in result

        assert table([]) == ""
        assert table([[]]) == ""

    def test_add_tab_space(self):
        assert add_tab_space("text", 0) == "text"
        assert add_tab_space("text", 1) == "    text"

        multiline = "line1\nline2"
        result = add_tab_space(multiline, 1)
        assert "    line1" in result
        assert "    line2" in result


@pytest.mark.asyncio
class TestImage:
    async def test_image_no_conversion(self):
        result = await image("photo", "https://example.com/image.png", False)
        assert "![photo](https://example.com/image.png)" == result

    async def test_image_base64_data(self):
        result = await image("photo", "data:image/png;base64,abc123", False)
        assert "![photo]" in result
        assert "data:" in result

    async def test_image_extracts_filename(self):
        result = await image("image", "https://example.com/photo.jpg", False)
        assert "photo.jpg" in result