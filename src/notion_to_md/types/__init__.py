"""Types for Notion to Markdown conversion."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union


# Type aliases
BlockAttributes = Dict[str, Any]
MdStringObject = Dict[str, str]
TextRequest = str
BlockType = str


@dataclass
class Annotations:
    """Text annotations from Notion rich text."""

    bold: bool = False
    italic: bool = False
    strikethrough: bool = False
    underline: bool = False
    code: bool = False
    color: str = "default"


@dataclass
class TextContent:
    """Content within a text element."""

    content: str
    link: Optional[Dict[str, Any]] = None


@dataclass
class Text:
    """Notion text element."""

    type: str = "text"
    text: Optional[TextContent] = None
    annotations: Optional[Annotations] = None
    plain_text: str = ""
    href: Optional[str] = None


@dataclass
class Equation:
    """Notion equation element."""

    type: str = "equation"
    equation: Optional[Dict[str, str]] = None
    annotations: Optional[Dict[str, Any]] = None
    plain_text: str = ""
    href: Optional[str] = None


@dataclass
class CalloutIcon:
    """Icon for callout blocks."""

    type: Optional[str] = None
    emoji: Optional[str] = None
    external: Optional[Dict[str, Any]] = None
    file: Optional[Dict[str, Any]] = None
    custom_emoji: Optional[Dict[str, Any]] = None


@dataclass
class MdBlock:
    """Markdown block representation."""

    type: Optional[str] = None
    blockId: str = ""
    parent: str = ""
    children: List["MdBlock"] = field(default_factory=list)


@dataclass
class ConfigurationOptions:
    """Configuration options for NotionToMarkdown."""

    separateChildPage: bool = False
    convertImagesToBase64: bool = False
    parseChildPages: bool = True


@dataclass
class NotionToMarkdownOptions:
    """Options for initializing NotionToMarkdown."""

    notion_client: Any  # Notion client instance
    config: Optional[ConfigurationOptions] = None


CustomTransformer = Callable[[Dict[str, Any]], Union[str, bool]]