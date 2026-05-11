# notion-to-md-python

Convert Notion pages to Markdown format.

## Installation

```bash
pip install notion-to-md
```

## Usage

```python
import asyncio
from notion_client import AsyncClient
from notion_to_md import NotionToMarkdown
from notion_to_md.types import NotionToMarkdownOptions

async def main():
    notion = AsyncClient(auth="your_notion_token")
    n2m = NotionToMarkdown(NotionToMarkdownOptions(notion_client=notion))

    md_blocks = await n2m.page_to_markdown("page_id")
    md_string = n2m.to_markdown_string(md_blocks)
    print(md_string["parent"])

asyncio.run(main())
```

## Configuration

```python
config = ConfigurationOptions(
    separateChildPage=False,      # Return child page content separately
    convertImagesToBase64=False,  # Download and embed images as base64
    parseChildPages=True          # Parse child page blocks
)
n2m = NotionToMarkdown(NotionToMarkdownOptions(notion_client=notion, config=config))
```

## License

ISC