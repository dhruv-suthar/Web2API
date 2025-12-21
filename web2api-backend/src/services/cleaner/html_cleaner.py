"""
HTML Cleaner Service

Converts HTML content to clean markdown using html2text.
Reduces token count by 60-80% compared to raw HTML.
"""

import logging
import html2text

logger = logging.getLogger(__name__)


def to_markdown(html: str) -> str:
    """
    Convert HTML content to clean markdown.
    
    This function uses html2text to convert HTML to markdown, which:
    - Removes HTML tags and formatting
    - Preserves text content and structure
    - Reduces token count by 60-80% compared to raw HTML
    - Maintains links (as markdown links)
    - Removes images (to reduce tokens)
    - Preserves emphasis (bold, italic)
    
    Args:
        html: Raw HTML string to convert
        
    Returns:
        Clean markdown string. Returns empty string if input is empty/invalid.
    """
    # Handle empty or None input
    if not html or not html.strip():
        logger.warn("Empty or invalid HTML provided to to_markdown")
        return ""
    
    try:
        # Configure html2text converter
        h = html2text.HTML2Text()
        
        # Configuration as specified in requirements:
        h.ignore_links = False      # Keep links as markdown links
        h.ignore_images = True       # Remove images to reduce tokens
        h.ignore_emphasis = False    # Keep bold/italic formatting
        h.body_width = 0             # No wrapping (preserve line breaks)
        
        # Additional useful settings:
        h.unicode_snob = True        # Use unicode characters
        h.escape_snob = False       # Don't escape special characters unnecessarily
        h.skip_internal_links = False  # Keep internal links
        h.inline_links = True        # Use inline links format [text](url)
        h.wrap_links = False         # Don't wrap links
        
        # Convert HTML to markdown
        markdown = h.handle(html)
        
        # Clean up extra whitespace (but preserve intentional line breaks)
        markdown = markdown.strip()
        
        logger.debug("HTML converted to markdown", {
            "html_length": len(html),
            "markdown_length": len(markdown),
            "reduction_percent": round((1 - len(markdown) / len(html)) * 100, 1) if html else 0
        })
        
        return markdown
        
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error("Error converting HTML to markdown", {
            "error": error_msg,
            "error_type": error_type,
            "html_length": len(html) if html else 0
        })
        
        # Return empty string on error (graceful degradation)
        # Could also return original HTML, but markdown is expected
        return ""

