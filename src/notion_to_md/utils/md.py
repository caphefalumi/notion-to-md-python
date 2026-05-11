"""Markdown rendering utilities."""

import base64
import re
import urllib.request
from typing import Optional

from notion_to_md.types import CalloutIcon


def inline_code(text: str) -> str:
    """Wrap text in inline code formatting."""
    return f"`{text}`"


def inline_equation(text: str) -> str:
    """Wrap text in inline equation formatting."""
    return f"${text}$"


def bold(text: str) -> str:
    """Make text bold."""
    return f"**{text}**"


def italic(text: str) -> str:
    """Make text italic."""
    return f"_{text}_"


def strikethrough(text: str) -> str:
    """Add strikethrough to text."""
    return f"~~{text}~~"


def underline(text: str) -> str:
    """Add underline to text."""
    return f"<u>{text}</u>"


def link(text: str, href: str) -> str:
    """Create a markdown link."""
    return f"[{text}]({href})"


def code_block(text: str, language: Optional[str] = None) -> str:
    """Create a fenced code block."""
    if not text:
        return ""
    lang = language.lower().strip() if language and language.strip() else "plaintext"
    return f"```{lang}\n{text.strip()}\n```"


def equation(text: str) -> str:
    """Create a block equation."""
    return f"$$\n{text}\n$$"


def heading1(text: str) -> str:
    """Create a level 1 heading."""
    return f"# {text}"


def heading2(text: str) -> str:
    """Create a level 2 heading."""
    return f"## {text}"


def heading3(text: str) -> str:
    """Create a level 3 heading."""
    return f"### {text}"


def quote(text: str) -> str:
    """Create a blockquote."""
    # Handle multiple lines
    return f"> {text.replace(chr(10), f"  \n> ")}"


def callout(text: str, icon: Optional[Any] = None) -> str:
    emoji = None
    if icon:
        icon_type = icon.get("type") if isinstance(icon, dict) else getattr(icon, "type", None)
        if icon_type == "emoji":
            emoji = icon.get("emoji") if isinstance(icon, dict) else getattr(icon, "emoji", None)

    formatted_text = text.replace("\n", "  \n> ")
    formatted_emoji = f"{emoji} " if emoji else ""

    # Handle headings within callout
    heading_match = re.match(r"^(#{1,6})\s+(.*)", formatted_text)
    if heading_match:
        heading_level = len(heading_match.group(1))
        heading_content = heading_match.group(2)
        return f"> {'#' * heading_level} {formatted_emoji}{heading_content}"

    return f"> {formatted_emoji}{formatted_text}"


def bullet(text: str, count: Optional[int] = None) -> str:
    """Create a bullet or numbered list item."""
    text = text.strip()
    return f"{count}. {text}" if count else f"- {text}"


def todo(text: str, checked: bool) -> str:
    """Create a todo item."""
    return f"- [x] {text}" if checked else f"- [ ] {text}"


async def image(
    alt: str, href: str, convert_to_base64: bool = False
) -> str:
    """Create an image markdown.

    Args:
        alt: Alt text for the image
        href: URL or data URI of the image
        convert_to_base64: Whether to download and convert to base64

    Returns:
        Markdown image string
    """
    # If not converting to base64 or already base64
    if not convert_to_base64 or href.startswith("data:"):
        if href.startswith("data:"):
            # Extract base64 data
            base64_data = href.split(",", 1)[-1] if "," in href else href
            # Override incorrect data format to png
            return f"![{alt}](data:image/png;base64,{base64_data})"
        return f"![{alt}]({href})"
    else:
        # Download image and convert to base64
        try:
            with urllib.request.urlopen(href) as response:
                data = response.read()
                base64_data = base64.b64encode(data).decode("utf-8")
                return f"![{alt}](data:image/png;base64,{base64_data})"
        except Exception:
            # If download fails, return regular link
            return f"![{alt}]({href})"


def add_tab_space(text: str, n: int = 0) -> str:
    """Add indentation to text.

    Args:
        text: Text to indent
        n: Number of indentation levels (4 spaces each)

    Returns:
        Indented text
    """
    tab = "    "
    for _ in range(n):
        if "\n" in text:
            text = tab + text.replace("\n", f"\n{tab}")
        else:
            text = tab + text
    return text


def divider() -> str:
    """Create a horizontal divider."""
    return "---"


def toggle(summary: Optional[str] = None, children: Optional[str] = None) -> str:
    """Create a toggle/collapsible block."""
    if not summary:
        return children or ""
    return f"<details>\n<summary>{summary}</summary>\n{children or ''}\n</details>\n\n"


def table(cells: list) -> str:
    """Create a markdown table.

    Args:
        cells: 2D array of cell values

    Returns:
        Markdown table string
    """
    if not cells or not cells[0]:
        return ""

    # Determine column widths
    col_count = len(cells[0])
    widths = [0] * col_count
    for row in cells:
        for i, cell in enumerate(row):
            if i < col_count:
                widths[i] = max(widths[i], len(str(cell)))

    # Build table
    lines = []

    for row_idx, row in enumerate(cells):
        line = "|"
        for i, cell in enumerate(row):
            if i < col_count:
                line += f" {str(cell).ljust(widths[i])} |"
            else:
                line += " |"
        lines.append(line)

        # Add header separator
        if row_idx == 0:
            sep = "|"
            for w in widths:
                sep += f" {'-' * w} |"
            lines.append(sep)

    return "\n".join(lines)