"""Tests for NotionToMarkdown class."""

import pytest
from notion_to_md import NotionToMarkdown
from notion_to_md.types import ConfigurationOptions, NotionToMarkdownOptions, MdBlock


class MockNotionClient:
    """Mock Notion client for testing."""

    def __init__(self, blocks_response):
        self._blocks_response = blocks_response

    @property
    def blocks(self):
        return self


class TestNotionToMarkdownInit:
    def test_default_config(self):
        mock_client = MockNotionClient([])
        options = NotionToMarkdownOptions(notion_client=mock_client)
        n2m = NotionToMarkdown(options)

        assert n2m.config.separateChildPage == False
        assert n2m.config.convertImagesToBase64 == False
        assert n2m.config.parseChildPages == True

    def test_custom_config(self):
        mock_client = MockNotionClient([])
        config = ConfigurationOptions(
            separateChildPage=True,
            convertImagesToBase64=True,
            parseChildPages=False,
        )
        options = NotionToMarkdownOptions(notion_client=mock_client, config=config)
        n2m = NotionToMarkdown(options)

        assert n2m.config.separateChildPage == True
        assert n2m.config.convertImagesToBase64 == True
        assert n2m.config.parseChildPages == False


class TestSetCustomTransformer:
    def test_set_custom_transformer(self):
        mock_client = MockNotionClient([])
        options = NotionToMarkdownOptions(notion_client=mock_client)
        n2m = NotionToMarkdown(options)

        def custom_handler(block):
            return "custom"

        n2m.set_custom_transformer("paragraph", custom_handler)
        assert "paragraph" in n2m.custom_transformers


class TestToMarkdownString:
    def test_empty_blocks(self):
        mock_client = MockNotionClient([])
        options = NotionToMarkdownOptions(notion_client=mock_client)
        n2m = NotionToMarkdown(options)

        result = n2m.to_markdown_string([])
        assert result == {}

    def test_heading_block(self):
        mock_client = MockNotionClient([])
        options = NotionToMarkdownOptions(notion_client=mock_client)
        n2m = NotionToMarkdown(options)

        blocks = [
            MdBlock(type="heading_1", blockId="123", parent="# Hello", children=[])
        ]

        result = n2m.to_markdown_string(blocks)
        assert "parent" in result
        assert "# Hello" in result["parent"]

    def test_bullet_list_items(self):
        mock_client = MockNotionClient([])
        options = NotionToMarkdownOptions(notion_client=mock_client)
        n2m = NotionToMarkdown(options)

        blocks = [
            MdBlock(type="bulleted_list_item", blockId="1", parent="- Item 1", children=[]),
            MdBlock(type="bulleted_list_item", blockId="2", parent="- Item 2", children=[]),
        ]

        result = n2m.to_markdown_string(blocks)
        assert "- Item 1" in result["parent"]
        assert "- Item 2" in result["parent"]

    def test_nested_blocks(self):
        mock_client = MockNotionClient([])
        options = NotionToMarkdownOptions(notion_client=mock_client)
        n2m = NotionToMarkdown(options)

        child_block = MdBlock(
            type="bulleted_list_item",
            blockId="2",
            parent="- Nested item",
            children=[]
        )
        parent_block = MdBlock(
            type="bulleted_list_item",
            blockId="1",
            parent="- Parent item",
            children=[child_block]
        )

        result = n2m.to_markdown_string([parent_block])
        assert "- Parent item" in result["parent"]
        assert "    - Nested item" in result["parent"]


class TestAnnotatePlainText:
    def test_annotations_basic(self):
        mock_client = MockNotionClient([])
        options = NotionToMarkdownOptions(notion_client=mock_client)
        n2m = NotionToMarkdown(options)

        result = n2m.annotate_plain_text("hello", {"bold": True})
        assert result == "**hello**"

    def test_annotations_multiple(self):
        mock_client = MockNotionClient([])
        options = NotionToMarkdownOptions(notion_client=mock_client)
        n2m = NotionToMarkdown(options)

        result = n2m.annotate_plain_text("code", {"code": True, "bold": True})
        assert "**" in result
        assert "`" in result

    def test_preserves_whitespace(self):
        mock_client = MockNotionClient([])
        options = NotionToMarkdownOptions(notion_client=mock_client)
        n2m = NotionToMarkdown(options)

        result = n2m.annotate_plain_text("  hello  ", {"bold": True})
        assert result.startswith("  ")
        assert result.endswith("  ")

    def test_empty_text(self):
        mock_client = MockNotionClient([])
        options = NotionToMarkdownOptions(notion_client=mock_client)
        n2m = NotionToMarkdown(options)

        result = n2m.annotate_plain_text("", {"bold": True})
        assert result == ""


class TestBlockToMarkdown:
    @pytest.mark.asyncio
    async def test_paragraph(self):
        mock_client = MockNotionClient([])
        options = NotionToMarkdownOptions(notion_client=mock_client)
        n2m = NotionToMarkdown(options)

        block = {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"plain_text": "Hello", "annotations": {}, "type": "text"}
                ]
            }
        }

        result = await n2m.block_to_markdown(block)
        assert result == "Hello"

    @pytest.mark.asyncio
    async def test_headings(self):
        mock_client = MockNotionClient([])
        options = NotionToMarkdownOptions(notion_client=mock_client)
        n2m = NotionToMarkdown(options)

        h1_block = {
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"plain_text": "Title", "annotations": {}, "type": "text"}]
            }
        }
        result = await n2m.block_to_markdown(h1_block)
        assert result == "# Title"

        h2_block = {
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"plain_text": "Subtitle", "annotations": {}, "type": "text"}]
            }
        }
        result = await n2m.block_to_markdown(h2_block)
        assert result == "## Subtitle"

        h3_block = {
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"plain_text": "Heading", "annotations": {}, "type": "text"}]
            }
        }
        result = await n2m.block_to_markdown(h3_block)
        assert result == "### Heading"

    @pytest.mark.asyncio
    async def test_divider(self):
        mock_client = MockNotionClient([])
        options = NotionToMarkdownOptions(notion_client=mock_client)
        n2m = NotionToMarkdown(options)

        block = {"type": "divider"}
        result = await n2m.block_to_markdown(block)
        assert result == "---"

    @pytest.mark.asyncio
    async def test_code_block(self):
        mock_client = MockNotionClient([])
        options = NotionToMarkdownOptions(notion_client=mock_client)
        n2m = NotionToMarkdown(options)

        block = {
            "type": "code",
            "code": {
                "rich_text": [{"plain_text": "print('hello')", "annotations": {}}],
                "language": "python"
            }
        }

        result = await n2m.block_to_markdown(block)
        assert "```python" in result
        assert "print('hello')" in result

    @pytest.mark.asyncio
    async def test_to_do(self):
        mock_client = MockNotionClient([])
        options = NotionToMarkdownOptions(notion_client=mock_client)
        n2m = NotionToMarkdown(options)

        unchecked_block = {
            "type": "to_do",
            "to_do": {
                "rich_text": [{"plain_text": "Task", "annotations": {}}],
                "checked": False
            }
        }
        result = await n2m.block_to_markdown(unchecked_block)
        assert "- [ ] Task" in result

        checked_block = {
            "type": "to_do",
            "to_do": {
                "rich_text": [{"plain_text": "Done", "annotations": {}}],
                "checked": True
            }
        }
        result = await n2m.block_to_markdown(checked_block)
        assert "- [x] Done" in result

    @pytest.mark.asyncio
    async def test_annotations(self):
        mock_client = MockNotionClient([])
        options = NotionToMarkdownOptions(notion_client=mock_client)
        n2m = NotionToMarkdown(options)

        block = {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"plain_text": "bold", "annotations": {"bold": True}, "type": "text"},
                    {"plain_text": " and ", "annotations": {}, "type": "text"},
                    {"plain_text": "italic", "annotations": {"italic": True}, "type": "text"},
                ]
            }
        }

        result = await n2m.block_to_markdown(block)
        assert "**bold**" in result
        assert "_italic_" in result

    @pytest.mark.asyncio
    async def test_link_in_text(self):
        mock_client = MockNotionClient([])
        options = NotionToMarkdownOptions(notion_client=mock_client)
        n2m = NotionToMarkdown(options)

        block = {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "plain_text": "Click here",
                        "annotations": {},
                        "href": "https://example.com",
                        "type": "text"
                    }
                ]
            }
        }

        result = await n2m.block_to_markdown(block)
        assert "[Click here](https://example.com)" in result

    @pytest.mark.asyncio
    async def test_image(self):
        mock_client = MockNotionClient([])
        options = NotionToMarkdownOptions(notion_client=mock_client)
        n2m = NotionToMarkdown(options)

        block = {
            "type": "image",
            "image": {
                "type": "external",
                "external": {"url": "https://example.com/image.png"},
                "caption": [{"plain_text": "My Image"}]
            }
        }

        result = await n2m.block_to_markdown(block)
        assert "![My Image]" in result
        assert "https://example.com/image.png" in result

    @pytest.mark.asyncio
    async def test_quote(self):
        mock_client = MockNotionClient([])
        options = NotionToMarkdownOptions(notion_client=mock_client)
        n2m = NotionToMarkdown(options)

        block = {
            "type": "quote",
            "quote": {
                "rich_text": [{"plain_text": "quoted text", "annotations": {}}]
            }
        }

        result = await n2m.block_to_markdown(block)
        assert "> quoted text" in result or "> quoted text" in result.replace("  \n> ", "\n")

    @pytest.mark.asyncio
    async def test_bulleted_list(self):
        mock_client = MockNotionClient([])
        options = NotionToMarkdownOptions(notion_client=mock_client)
        n2m = NotionToMarkdown(options)

        block = {
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"plain_text": "List item", "annotations": {}}]
            }
        }

        result = await n2m.block_to_markdown(block)
        assert "- List item" in result

    @pytest.mark.asyncio
    async def test_numbered_list(self):
        mock_client = MockNotionClient([])
        options = NotionToMarkdownOptions(notion_client=mock_client)
        n2m = NotionToMarkdown(options)

        block = {
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [{"plain_text": "Numbered item", "annotations": {}}],
                "number": 1
            }
        }

        result = await n2m.block_to_markdown(block)
        assert "1. Numbered item" in result

    @pytest.mark.asyncio
    async def test_callout(self):
        mock_client = MockNotionClient([])
        options = NotionToMarkdownOptions(notion_client=mock_client)
        n2m = NotionToMarkdown(options)

        block = {
            "type": "callout",
            "callout": {
                "rich_text": [{"plain_text": "Info", "annotations": {}}],
                "icon": {"type": "emoji", "emoji": "💡"}
            },
            "has_children": False
        }

        result = await n2m.block_to_markdown(block)
        assert "💡" in result
        assert "Info" in result

    @pytest.mark.asyncio
    async def test_unsupported_skipped(self):
        mock_client = MockNotionClient([])
        options = NotionToMarkdownOptions(notion_client=mock_client)
        n2m = NotionToMarkdown(options)

        blocks = await n2m.blocks_to_markdown([{"type": "unsupported"}])
        assert len(blocks) == 0

    @pytest.mark.asyncio
    async def test_child_page_disabled(self):
        mock_client = MockNotionClient([])
        config = ConfigurationOptions(parseChildPages=False)
        options = NotionToMarkdownOptions(notion_client=mock_client, config=config)
        n2m = NotionToMarkdown(options)

        blocks = await n2m.blocks_to_markdown([
            {"type": "child_page", "id": "123", "has_children": True}
        ])
        assert len(blocks) == 0