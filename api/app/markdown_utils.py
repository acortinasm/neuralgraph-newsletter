"""Markdown processing utilities."""
import markdown
from markdown.extensions import fenced_code, tables, toc, nl2br


def render_markdown(content: str) -> str:
    """
    Render markdown to HTML with common extensions.

    Extensions enabled:
    - fenced_code: ```code blocks```
    - tables: GitHub-style tables
    - toc: Table of contents with [TOC]
    - nl2br: Newlines become <br>
    """
    md = markdown.Markdown(
        extensions=[
            "fenced_code",
            "tables",
            "toc",
            "nl2br",
            "smarty",  # Smart quotes
            "sane_lists",  # Better list handling
        ],
        output_format="html5"
    )
    return md.convert(content)


def extract_excerpt(content: str, max_length: int = 200) -> str:
    """Extract a plain text excerpt from markdown content."""
    import re

    # Remove markdown formatting
    text = content

    # Remove headers
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

    # Remove emphasis
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)

    # Remove links but keep text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # Remove images
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", "", text)

    # Remove code blocks
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`[^`]+`", "", text)

    # Remove blockquotes
    text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)

    # Remove horizontal rules
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Truncate
    if len(text) > max_length:
        text = text[:max_length].rsplit(" ", 1)[0] + "..."

    return text
