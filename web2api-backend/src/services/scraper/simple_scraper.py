"""
Simple Scraper Service (Fallback)

Lightweight fallback scraper for static HTML sites.
Uses simple HTTP requests - no JavaScript rendering, no anti-bot protection.
Best for static sites or when Firecrawl is unavailable.
"""

import logging
from typing import Dict, Optional, Any
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError, HTTPError

logger = logging.getLogger(__name__)

# Default User-Agent string (standard browser)
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


async def scrape(url: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Scrape URL using simple HTTP request.
    
    This is a lightweight fallback scraper that:
    - Uses requests.get() with standard headers
    - Returns raw HTML content
    - Cannot execute JavaScript
    - No anti-bot protection
    
    Args:
        url: Target URL to scrape
        options: Optional dictionary with scraping options:
            - timeout: Request timeout in seconds (default: 30)
            - headers: Custom headers dictionary (User-Agent will be added if not provided)
            - user_agent: Custom User-Agent string (default: standard browser UA)
    
    Returns:
        Dictionary with:
            - html: str - Raw HTML content
            - success: bool - Whether scraping succeeded
            - error: str (optional) - Error message if failed
    
    Raises:
        ValueError: If URL is invalid or empty
    """
    if not url or not url.strip():
        logger.error("Invalid URL provided", {"url": url})
        raise ValueError("URL cannot be empty")
    
    # Normalize URL
    url = url.strip()
    
    # Parse options with defaults
    options = options or {}
    timeout_seconds = options.get("timeout", 30)
    custom_headers = options.get("headers", {})
    user_agent = options.get("user_agent", DEFAULT_USER_AGENT)
    
    # Build headers with User-Agent
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        **custom_headers  # Allow custom headers to override defaults
    }
    
    logger.info("Starting simple HTTP scrape", {
        "url": url,
        "timeout": timeout_seconds,
        "user_agent": user_agent[:50] + "..." if len(user_agent) > 50 else user_agent
    })
    
    try:
        # Make HTTP GET request
        response = requests.get(
            url,
            headers=headers,
            timeout=timeout_seconds,
            allow_redirects=True
        )
        
        # Raise an exception for bad status codes (4xx, 5xx)
        response.raise_for_status()
        
        # Get HTML content
        html = response.text
        
        logger.info("Simple HTTP scrape completed successfully", {
            "url": url,
            "status_code": response.status_code,
            "html_length": len(html),
            "content_type": response.headers.get("Content-Type", "unknown")
        })
        
        return {
            "html": html,
            "success": True
        }
        
    except Timeout as e:
        error_msg = f"Request timeout after {timeout_seconds} seconds"
        logger.error("Request timeout", {
            "url": url,
            "timeout": timeout_seconds,
            "error": str(e)
        })
        return {
            "html": "",
            "success": False,
            "error": error_msg
        }
        
    except ConnectionError as e:
        error_msg = f"Connection error: {str(e)}"
        logger.error("Connection error", {
            "url": url,
            "error": str(e),
            "error_type": type(e).__name__
        })
        return {
            "html": "",
            "success": False,
            "error": error_msg
        }
        
    except HTTPError as e:
        status_code = e.response.status_code if e.response else None
        error_msg = f"HTTP error {status_code}: {str(e)}"
        
        # Handle 404 specifically
        if status_code == 404:
            error_msg = f"Page not found (404): {url}"
            logger.warn("Page not found", {
                "url": url,
                "status_code": 404
            })
        else:
            logger.error("HTTP error", {
                "url": url,
                "status_code": status_code,
                "error": str(e)
            })
        
        return {
            "html": "",
            "success": False,
            "error": error_msg
        }
        
    except RequestException as e:
        error_msg = f"Request error: {str(e)}"
        logger.error("Request exception", {
            "url": url,
            "error": str(e),
            "error_type": type(e).__name__
        })
        return {
            "html": "",
            "success": False,
            "error": error_msg
        }
        
    except ValueError as e:
        error_msg = str(e)
        logger.error("Invalid URL provided", {
            "url": url,
            "error": error_msg
        })
        return {
            "html": "",
            "success": False,
            "error": f"Invalid URL: {error_msg}"
        }
        
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error("Unexpected error during simple HTTP scrape", {
            "url": url,
            "error": error_msg,
            "error_type": error_type
        })
        return {
            "html": "",
            "success": False,
            "error": f"Unexpected error: {error_msg}"
        }

