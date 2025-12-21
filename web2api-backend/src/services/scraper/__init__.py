"""
Scraper services for web content extraction.

This module provides scrapers for fetching web content:
- Firecrawl scraper (primary) - for JS-heavy sites with anti-bot protection
- Simple scraper (fallback) - for static HTML sites
"""

from .firecrawl_scraper import scrape as firecrawl_scrape
from .simple_scraper import scrape as simple_scrape

__all__ = ["firecrawl_scrape", "simple_scrape"]

