"""Notion API helpers."""

from typing import Any, Dict, List, Optional


async def get_block_children(
    notion_client: Any, block_id: str, total_page: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Get all children of a block with pagination.

    Args:
        notion_client: Notion client instance
        block_id: ID of the block to get children for
        total_page: Maximum number of pages to fetch (None for all)

    Returns:
        List of block objects
    """
    result = []
    page_count = 0
    start_cursor = None

    while True:
        params = {
            "start_cursor": start_cursor,
            "block_id": block_id,
        }
        if hasattr(notion_client, "blocks") and hasattr(notion_client.blocks, "children"):
            response = await notion_client.blocks.children.list(**params)
        else:
            # Sync client compatibility
            response = notion_client.blocks.children.list(**params)

        result.extend(response.get("results", []))

        start_cursor = response.get("next_cursor")
        page_count += 1

        if start_cursor is None or (total_page is not None and page_count >= total_page):
            break

    modify_numbered_list_object(result)
    return result


def modify_numbered_list_object(blocks: List[Dict[str, Any]]) -> None:
    """Assign sequential numbers to numbered list items.

    Args:
        blocks: List of block objects to modify in place
    """
    numbered_list_index = 0

    for block in blocks:
        block_type = block.get("type")
        if block_type == "numbered_list_item":
            numbered_list_index += 1
            if "numbered_list_item" in block:
                block["numbered_list_item"]["number"] = numbered_list_index
        else:
            numbered_list_index = 0