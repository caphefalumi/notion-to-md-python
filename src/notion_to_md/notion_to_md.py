"""Notion to Markdown converter main class."""

import re
from typing import Any, Callable, Dict, List, Optional, Union

from notion_to_md.types import (
    CalloutIcon,
    ConfigurationOptions,
    CustomTransformer,
    MdBlock,
    MdStringObject,
    NotionToMarkdownOptions,
)
from notion_to_md.utils import md
from notion_to_md.utils.notion import get_block_children


class NotionToMarkdown:
    """Converts Notion pages to Markdown format."""

    def __init__(self, options: NotionToMarkdownOptions) -> None:
        self.notion_client = options.notion_client
        default_config = ConfigurationOptions(
            separateChildPage=False,
            convertImagesToBase64=False,
            parseChildPages=True,
        )
        if options.config:
            self.config = ConfigurationOptions(
                separateChildPage=options.config.separateChildPage,
                convertImagesToBase64=options.config.convertImagesToBase64,
                parseChildPages=options.config.parseChildPages,
            )
        else:
            self.config = default_config
        self.custom_transformers: Dict[str, CustomTransformer] = {}

    def set_custom_transformer(
        self, block_type: str, transformer: CustomTransformer
    ) -> "NotionToMarkdown":
        self.custom_transformers[block_type] = transformer
        return self

    def to_markdown_string(
        self,
        md_blocks: List[MdBlock] = None,
        page_identifier: str = "parent",
        nesting_level: int = 0,
    ) -> MdStringObject:
        if md_blocks is None:
            md_blocks = []
        md_output: MdStringObject = {}

        for md_block in md_blocks:
            block_type = md_block.type or ""
            parent_content = md_block.parent or ""
            children = md_block.children or []

            # Process parent blocks
            if md_block.parent and block_type not in ("toggle", "child_page"):
                if block_type not in ("to_do", "bulleted_list_item", "numbered_list_item", "quote"):
                    md_output[page_identifier] = md_output.get(page_identifier, "")
                    md_output[page_identifier] += f"\n{md.add_tab_space(parent_content, nesting_level)}\n\n"
                else:
                    md_output[page_identifier] = md_output.get(page_identifier, "")
                    md_output[page_identifier] += f"{md.add_tab_space(parent_content, nesting_level)}\n"

            # Process child blocks
            if children:
                if block_type in ("synced_block", "column_list", "column"):
                    child_md = self.to_markdown_string(children, page_identifier)
                    md_output[page_identifier] = md_output.get(page_identifier, "")
                    for key, value in child_md.items():
                        if key in md_output:
                            md_output[key] += value
                        else:
                            md_output[key] = value

                elif block_type == "child_page":
                    child_page_title = md_block.parent or "child_page"
                    child_md = self.to_markdown_string(children, child_page_title)
                    if self.config.separateChildPage:
                        md_output.update(child_md)
                    else:
                        md_output[page_identifier] = md_output.get(page_identifier, "")
                        if child_page_title in child_md:
                            md_output[page_identifier] += f"\n{child_page_title}\n{child_md[child_page_title]}"

                elif block_type == "toggle":
                    toggle_children_md = self.to_markdown_string(children)
                    md_output[page_identifier] = md_output.get(page_identifier, "")
                    md_output[page_identifier] += md.toggle(
                        md_block.parent,
                        toggle_children_md.get("parent", "")
                    )

                elif block_type == "quote":
                    quote_children_md = self.to_markdown_string(
                        children, page_identifier, nesting_level
                    )
                    parent_key = "parent" if page_identifier != "parent" else page_identifier
                    content = quote_children_md.get(parent_key, quote_children_md.get(page_identifier, ""))
                    formatted = "\n".join(
                        f"> {line}" if line.strip() else ">"
                        for line in content.split("\n")
                    ).strip()
                    md_output[page_identifier] = md_output.get(page_identifier, "")
                    md_output[page_identifier] += formatted + "\n"

                elif block_type == "callout":
                    pass

                else:
                    child_md = self.to_markdown_string(children, page_identifier, nesting_level + 1)
                    md_output[page_identifier] = md_output.get(page_identifier, "")
                    if page_identifier != "parent" and "parent" in child_md:
                        md_output[page_identifier] += child_md["parent"]
                    elif page_identifier in child_md:
                        md_output[page_identifier] += child_md[page_identifier]

        return md_output

    async def page_to_markdown(
        self, page_id: str, total_page: Optional[int] = None
    ) -> List[MdBlock]:
        if not self.notion_client:
            raise ValueError(
                "notion client is not provided, for more details check out https://github.com/souvikinator/notion-to-md"
            )
        blocks = await get_block_children(self.notion_client, page_id, total_page)
        parsed_data = await self.blocks_to_markdown(blocks)
        return parsed_data

    async def blocks_to_markdown(
        self,
        blocks: Optional[List[Dict[str, Any]]] = None,
        total_page: Optional[int] = None,
        md_blocks: Optional[List[MdBlock]] = None,
    ) -> List[MdBlock]:
        if md_blocks is None:
            md_blocks = []
        if not self.notion_client:
            raise ValueError(
                "notion client is not provided, for more details check out https://github.com/souvikinator/notion-to-md"
            )
        if not blocks:
            return md_blocks

        for block in blocks:
            block_type = block.get("type", "")

            if block_type in ("unsupported",) or (
                block_type == "child_page" and not self.config.parseChildPages
            ):
                continue

            has_children = block.get("has_children", False)

            if has_children:
                block_id = block.get("id", "")
                if block_type == "synced_block":
                    synced_from = block.get("synced_block", {}).get("synced_from", {})
                    if synced_from and synced_from.get("block_id"):
                        block_id = synced_from["block_id"]

                child_blocks = await get_block_children(self.notion_client, block_id, total_page)

                md_block = MdBlock(
                    type=block_type,
                    blockId=block.get("id", ""),
                    parent=await self.block_to_markdown(block),
                    children=[],
                )
                md_blocks.append(md_block)

                if block_type not in self.custom_transformers:
                    child_md = await self.blocks_to_markdown(
                        child_blocks, total_page, []
                    )
                    md_blocks[-1].children = child_md

                continue

            tmp = await self.block_to_markdown(block)
            md_blocks.append(
                MdBlock(
                    type=block_type,
                    blockId=block.get("id", ""),
                    parent=tmp,
                    children=[],
                )
            )

        return md_blocks

    async def block_to_markdown(self, block: Dict[str, Any]) -> str:
        if not isinstance(block, dict) or "type" not in block:
            return ""

        parsed_data = ""
        block_type = block.get("type", "")

        if block_type in self.custom_transformers:
            result = self.custom_transformers[block_type](block)
            if isinstance(result, str):
                return result

        if block_type == "image":
            block_content = block.get("image", {})
            image_title = "image"
            caption = block_content.get("caption", [])
            if isinstance(caption, list):
                image_caption_plain = "".join(
                    item.get("plain_text", "") for item in caption
                )
            else:
                image_caption_plain = ""

            image_type = block_content.get("type", "external")
            link = ""

            if image_type == "external":
                link = block_content.get("external", {}).get("url", "")
            if image_type == "file":
                link = block_content.get("file", {}).get("url", "")

            if image_caption_plain.strip():
                image_title = image_caption_plain
            elif link:
                matches = re.findall(r"[^\/\\&\?]+\.\w{3,4}(?=([\?&].*$|$))", link)
                image_title = matches[0] if matches else image_title

            return await md.image(
                image_title,
                link,
                self.config.convertImagesToBase64,
            )

        elif block_type == "divider":
            return md.divider()

        elif block_type == "equation":
            expr = block.get("equation", {}).get("expression", "")
            return md.equation(expr)

        elif block_type in ("video", "file", "pdf"):
            if block_type == "video":
                block_content = block.get("video")
            elif block_type == "file":
                block_content = block.get("file")
            else:
                block_content = block.get("pdf")

            if block_content:
                caption = block_content.get("caption", [])
                title = block_type
                if isinstance(caption, list):
                    title = "".join(item.get("plain_text", "") for item in caption) or block_type

                file_type = block_content.get("type", "external")
                link = ""
                if file_type == "external":
                    link = block_content.get("external", {}).get("url", "")
                if file_type == "file":
                    link = block_content.get("file", {}).get("url", "")

                if not title.strip():
                    matches = re.findall(r"[^\/\\&\?]+\.\w{3,4}(?=([\?&].*$|$))", link)
                    title = matches[0] if matches else block_type

                return md.link(title, link)
            return ""

        elif block_type in ("bookmark", "embed", "link_preview", "link_to_page"):
            block_content = None
            title = block_type

            if block_type == "bookmark":
                block_content = block.get("bookmark")
                title = "bookmark"
            elif block_type == "embed":
                block_content = block.get("embed")
                title = "embed"
            elif block_type == "link_preview":
                block_content = block.get("link_preview")
                title = "link_preview"
            elif block_type == "link_to_page":
                link_to_page = block.get("link_to_page", {})
                if link_to_page.get("type") == "page_id":
                    page_id = link_to_page.get("page_id", "")
                    block_content = {"url": f"https://www.notion.so/{page_id}"}
                    title = "link_to_page"

            if block_content and block_content.get("url"):
                return md.link(title, block_content["url"])
            return ""

        elif block_type == "child_page":
            if not self.config.parseChildPages:
                return ""
            page_title = block.get("child_page", {}).get("title", "child_page")
            if self.config.separateChildPage:
                return page_title
            return md.heading2(page_title)

        elif block_type == "child_database":
            page_title = block.get("child_database", {}).get("title") or "child_database"
            return page_title

        elif block_type == "table":
            table_id = block.get("id", "")
            has_children = block.get("has_children", False)
            table_arr: List[List[str]] = []

            if has_children:
                table_rows = await get_block_children(self.notion_client, table_id, 100)
                for row in table_rows:
                    if row.get("type") != "table_row":
                        continue
                    cells = row.get("table_row", {}).get("cells", [])
                    cell_strings = []
                    for cell in cells:
                        cell_block = {
                            "type": "paragraph",
                            "paragraph": {"rich_text": cell},
                        }
                        cell_str = await self.block_to_markdown(cell_block)
                        cell_strings.append(cell_str)
                    table_arr.append(cell_strings)

            return md.table(table_arr)

        else:
            block_content_list = []
            type_data = block.get(block_type, {})

            if isinstance(type_data, dict):
                if "text" in type_data:
                    block_content_list = type_data["text"]
                elif "rich_text" in type_data:
                    block_content_list = type_data["rich_text"]

            for content in block_content_list:
                if not isinstance(content, dict):
                    continue

                if content.get("type") == "equation":
                    expr = content.get("equation", {}).get("expression", "")
                    parsed_data += md.inline_equation(expr)
                    continue

                annotations = content.get("annotations", {})
                plain_text = content.get("plain_text", "")

                plain_text = self.annotate_plain_text(plain_text, annotations)

                href = content.get("href")
                if href:
                    plain_text = md.link(plain_text, href)

                parsed_data += plain_text

        # Post-processing for specific block types
        if block_type == "code":
            rich_text = block.get("code", {}).get("rich_text", [])
            code_content = "".join(t.get("plain_text", "") for t in rich_text)
            language = block.get("code", {}).get("language", "plaintext")
            parsed_data = md.code_block(code_content, language)

        elif block_type == "heading_1":
            parsed_data = md.heading1(parsed_data)
        elif block_type == "heading_2":
            parsed_data = md.heading2(parsed_data)
        elif block_type == "heading_3":
            parsed_data = md.heading3(parsed_data)
        elif block_type == "quote":
            parsed_data = md.quote(parsed_data)
        elif block_type == "callout":
            callout_id = block.get("id", "")
            has_children = block.get("has_children", False)
            icon_data = block.get("callout", {}).get("icon")

            if not has_children:
                return md.callout(parsed_data, icon_data)

            callout_children_obj = await get_block_children(self.notion_client, callout_id, 100)
            callout_children = await self.blocks_to_markdown(callout_children_obj)

            callout_string = parsed_data + "\n"
            for child in callout_children:
                if child.parent:
                    callout_string += child.parent + "\n\n"

            return md.callout(callout_string.strip(), icon_data)

        elif block_type == "bulleted_list_item":
            parsed_data = md.bullet(parsed_data)
        elif block_type == "numbered_list_item":
            number = block.get("numbered_list_item", {}).get("number")
            parsed_data = md.bullet(parsed_data, number)
        elif block_type == "to_do":
            checked = block.get("to_do", {}).get("checked", False)
            parsed_data = md.todo(parsed_data, checked)

        return parsed_data

    def annotate_plain_text(self, text: str, annotations: Dict[str, Any]) -> str:
        if not text or text.isspace():
            return text

        leading_match = re.match(r"^(\s*)", text)
        trailing_match = re.search(r"(\s*)$", text)
        leading_space = leading_match.group(1) if leading_match else ""
        trailing_space = trailing_match.group(1) if trailing_match else ""

        text = text.strip()

        if text:
            if annotations.get("code"):
                text = md.inline_code(text)
            if annotations.get("bold"):
                text = md.bold(text)
            if annotations.get("italic"):
                text = md.italic(text)
            if annotations.get("strikethrough"):
                text = md.strikethrough(text)
            if annotations.get("underline"):
                text = md.underline(text)

        return leading_space + text + trailing_space