"""
Firecrawl Scraper Service

Primary scraper using Firecrawl API for JS-heavy sites.
Handles JavaScript rendering, anti-bot protection, and proxy rotation.
"""

import os
import logging
from typing import Dict, Optional, Any
from firecrawl.v2.client import FirecrawlClient
from firecrawl.v2.utils.error_handler import FirecrawlError

logger = logging.getLogger(__name__)


async def scrape(url: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Scrape URL using Firecrawl API.
    
    Args:
        url: Target URL to scrape
        options: Optional dictionary with scraping options:
            - timeout: Request timeout in milliseconds (default: 30000)
            - wait_for: Wait time in milliseconds for JS to render (default: 2000)
            - formats: List of formats to scrape (default: ["markdown", "html"])
            - headers: Custom headers dictionary
            - only_main_content: Whether to only scrape main content (default: True)
    
    Returns:
        Dictionary with:
            - html: str - Raw HTML content
            - metadata: dict - Page metadata (title, description, etc.)
            - success: bool - Whether scraping succeeded
            - error: str (optional) - Error message if failed
    
    Raises:
        ValueError: If URL is invalid or empty
        FirecrawlError: If Firecrawl API call fails
    """
    if not url or not url.strip():
        logger.error("Invalid URL provided", {"url": url})
        raise ValueError("URL cannot be empty")
    
    # Normalize URL
    url = url.strip()
    
    # Get API key from environment
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        logger.error("FIRECRAWL_API_KEY not set in environment")
        return {
            "html": "",
            "metadata": {},
            "success": False,
            "error": "FIRECRAWL_API_KEY environment variable not set"
        }
    
    # Parse options with defaults
    # Note: Firecrawl API expects timeout and wait_for in MILLISECONDS
    # Important: wait_for must not exceed half of timeout
    options = options or {}
    timeout_ms = options.get("timeout", 30000)  # 30 seconds default
    wait_for_ms = options.get("wait_for", 2000)  # 2 seconds default
    formats = options.get("formats", ["markdown", "html"])
    headers = options.get("headers")
    only_main_content = options.get("only_main_content", True)
    
    # Validate: wait_for must not exceed half of timeout (Firecrawl requirement)
    if wait_for_ms > timeout_ms / 2:
        logger.warning("wait_for exceeds half of timeout, capping it", {
            "original_wait_for_ms": wait_for_ms,
            "timeout_ms": timeout_ms,
            "capped_wait_for_ms": int(timeout_ms / 2)
        })
        wait_for_ms = int(timeout_ms / 2)
    
    # Convert timeout to seconds for the HTTP client (not the API parameter)
    client_timeout_seconds = timeout_ms / 1000 if timeout_ms else None
    
    logger.info("Starting Firecrawl scrape", {
        "url": url,
        "timeout_ms": timeout_ms,
        "wait_for_ms": wait_for_ms,
        "formats": formats
    })
    
    try:
        # Initialize Firecrawl client (client timeout in seconds for HTTP requests)
        client = FirecrawlClient(api_key=api_key, timeout=client_timeout_seconds)
        
        # Scrape URL
        # Note: Firecrawl API expects timeout and wait_for in MILLISECONDS
        document = client.scrape(
            url,
            formats=formats,
            wait_for=wait_for_ms,
            timeout=timeout_ms,  # Pass milliseconds, not seconds!
            headers=headers,
            only_main_content=only_main_content
        )
        
        # Extract content and metadata
        html = getattr(document, "html", "") or ""
        markdown = getattr(document, "markdown", "") or ""
        metadata = {}
        
        # Extract metadata if available
        if hasattr(document, "metadata") and document.metadata:
            metadata = {
                "title": getattr(document.metadata, "title", None),
                "description": getattr(document.metadata, "description", None),
                "url": getattr(document.metadata, "url", url),
                "source_url": getattr(document.metadata, "source_url", url),
                "language": getattr(document.metadata, "language", None),
                "status_code": getattr(document.metadata, "status_code", None),
                "content_type": getattr(document.metadata, "content_type", None),
            }
            # Include any additional metadata fields
            if hasattr(document.metadata, "extras"):
                metadata.update(document.metadata.extras)
        
        # Prefer HTML if available, otherwise use markdown
        # (html2text will convert HTML to markdown later if needed)
        content_html = html if html else ""
        
        logger.info("Firecrawl scrape completed successfully", {
            "url": url,
            "html_length": len(content_html),
            "markdown_length": len(markdown),
            "has_metadata": bool(metadata)
        })
        
        return {
            "html": content_html,
            "markdown": markdown,  # Also return markdown for convenience
            "metadata": metadata,
            "success": True
        }
        
    except FirecrawlError as e:
        error_msg = str(e)
        logger.error("Firecrawl API error", {
            "url": url,
            "error": error_msg,
            "error_type": type(e).__name__
        })
        
        # Check for specific error types
        if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
            return {
                "html": "",
                "metadata": {},
                "success": False,
                "error": f"Request timeout: {error_msg}"
            }
        elif "rate limit" in error_msg.lower() or "429" in error_msg:
            return {
                "html": "",
                "metadata": {},
                "success": False,
                "error": f"Rate limit exceeded: {error_msg}"
            }
        elif "invalid" in error_msg.lower() or "404" in error_msg or "not found" in error_msg.lower():
            return {
                "html": "",
                "metadata": {},
                "success": False,
                "error": f"Invalid URL or page not found: {error_msg}"
            }
        else:
            return {
                "html": "",
                "metadata": {},
                "success": False,
                "error": f"Firecrawl error: {error_msg}"
            }
            
    except ValueError as e:
        error_msg = str(e)
        logger.error("Invalid URL provided", {
            "url": url,
            "error": error_msg
        })
        return {
            "html": "",
            "metadata": {},
            "success": False,
            "error": f"Invalid URL: {error_msg}"
        }
        
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error("Unexpected error during Firecrawl scrape", {
            "url": url,
            "error": error_msg,
            "error_type": error_type
        })
        return {
            "html": "",
            "metadata": {},
            "success": False,
            "error": f"Unexpected error: {error_msg}"
        }

