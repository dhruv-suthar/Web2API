"""
Fetch Webpage Event Step

Subscribes to extraction.requested events.

Flow:
1. Check extraction cache (url + schema) → If hit, emit extraction.completed directly
2. Check content cache (url only) → If hit, skip Firecrawl
3. Scrape with Firecrawl if needed
4. Store markdown in state (to avoid 4KB event limit)
5. Emit webpage.fetched for LLM extraction

Optimized for Motia Cloud:
- Event payloads kept under 4KB limit
- Large data (markdown, schema) stored in state
"""

from typing import Dict, Any

# Import services - paths relative to project root for Motia bundling
from src.utils.hash_utils import hash_url_full
from src.services.scraper.firecrawl_scraper import scrape as firecrawl_scrape
from src.services.scraper.simple_scraper import scrape as simple_scrape
from src.services.cleaner.html_cleaner import to_markdown
from src.services.progress.progress_service import update_progress
from src.services.cache.cache_service import get_cached_extraction


# Input schema - minimal payload, large data fetched from state
input_schema = {
    "type": "object",
    "properties": {
        "job_id": {"type": "string"},
        "url": {"type": "string"},
        "scraper_id": {"type": "string"},
        "options": {
            "type": "object",
            "properties": {
                "use_cache": {"type": "boolean", "default": True},
                "use_simple_scraper": {"type": "boolean", "default": False},
                "timeout": {"type": "integer", "default": 30000},
                "wait_for": {"type": "integer", "default": 2000}
            }
        }
    },
    "required": ["job_id", "url"]
}

config = {
    "name": "FetchWebpage",
    "type": "event",
    "description": "Fetches webpage, checks cache, and triggers extraction",
    "subscribes": ["extraction.requested"],
    "emits": ["webpage.fetched", "extraction.completed", "extraction.failed"],
    "flows": ["extraction-flow"],
    "input": input_schema,
    # Include service/util dependencies for Motia Cloud deployment
    # Paths are relative from steps/events/ to src/
    "includeFiles": [
        "../../src/utils/__init__.py",
        "../../src/utils/hash_utils.py",
        "../../src/services/__init__.py",
        "../../src/services/scraper/__init__.py",
        "../../src/services/scraper/firecrawl_scraper.py",
        "../../src/services/scraper/simple_scraper.py",
        "../../src/services/cleaner/__init__.py",
        "../../src/services/cleaner/html_cleaner.py",
        "../../src/services/progress/__init__.py",
        "../../src/services/progress/progress_service.py",
        "../../src/services/cache/__init__.py",
        "../../src/services/cache/cache_service.py",
    ],
    # Motia Cloud infrastructure config
    "infrastructure": {
        "handler": {
            "ram": 512,
            "timeout": 60
        },
        "queue": {
            "type": "fifo",
            "maxRetries": 3,
            "visibilityTimeout": 90
        }
    }
}


async def handler(input_data: Dict[str, Any], context) -> None:
    """
    Handler for fetching webpage content.
    Stores large data in state to comply with 4KB event payload limit.
    """
    job_id = input_data.get("job_id", "unknown")
    url = input_data.get("url", "").strip()
    scraper_id = input_data.get("scraper_id")
    options = input_data.get("options", {})
    
    try:
        # 1. Validate input
        if not job_id or job_id == "unknown":
            await emit_failure(context, job_id, "job_id is required", "fetching")
            return
        
        if not url:
            await emit_failure(context, job_id, "url is required", "fetching")
            return
        
        # 2. Fetch schema from state (stored by run_scraper_step)
        job_data_result = await context.state.get("job_payloads", job_id)
        if not job_data_result:
            await emit_failure(context, job_id, "Job payload not found in state", "fetching")
            return
        
        # Unwrap the 'data' property if Motia state wraps it
        job_data = job_data_result.get("data", job_data_result) if isinstance(job_data_result, dict) else job_data_result
        schema = job_data.get("schema")
        if not schema:
            await emit_failure(context, job_id, "schema is required", "fetching")
            return
        
        # 3. Parse options
        use_cache = options.get("use_cache", True)
        use_simple_scraper = options.get("use_simple_scraper", False)
        timeout = options.get("timeout", 30000)
        wait_for = options.get("wait_for", 2000)
        
        context.logger.info("Processing extraction request", {
            "job_id": job_id, 
            "url": url,
            "use_cache": use_cache
        })
        
        # 4. Check EXTRACTION cache first (skip both Firecrawl AND OpenAI)
        if use_cache:
            cached_extraction = await get_cached_extraction(context.state, url, schema)
            
            if cached_extraction:
                context.logger.info("Extraction cache hit - skipping Firecrawl and OpenAI", {
                    "job_id": job_id,
                    "url": url,
                    "cached_at": cached_extraction.get("cached_at")
                })
                
                await update_progress(context.streams, job_id, "completed", 100, "Using cached result")
                
                # Store result in state for store_results_step
                await context.state.set("extraction_payloads", job_id, {
                    "data": cached_extraction.get("data"),
                    "schema": schema,
                    "model": cached_extraction.get("model"),
                    "metadata": cached_extraction.get("metadata", {})
                })
                
                # Emit minimal payload - data fetched from state by next step
                await context.emit({
                    "topic": "extraction.completed",
                    "data": {
                        "job_id": job_id,
                        "url": url,
                        "scraper_id": scraper_id,
                        "cached": True,
                        "cache_type": "extraction"
                    }
                })
                return
        
        # 5. Check CONTENT cache (skip Firecrawl only)
        await update_progress(context.streams, job_id, "fetching", 20, "Fetching webpage...")
        
        url_hash = hash_url_full(url)
        content_cached = False
        markdown = None
        metadata = {}
        
        if use_cache:
            cached_result = await context.state.get("content_cache", url_hash)
            if cached_result:
                cached_data = cached_result.get("data", cached_result) if isinstance(cached_result, dict) else cached_result
                if cached_data and cached_data.get("markdown"):
                    markdown = cached_data.get("markdown", "")
                    metadata = cached_data.get("metadata", {})
                    content_cached = True
                    context.logger.info("Content cache hit - skipping Firecrawl", {
                        "job_id": job_id,
                        "url": url
                    })
        
        # 6. Scrape if no content cache
        if not markdown:
            scraper_type = "simple" if use_simple_scraper else "firecrawl"
            context.logger.info("Scraping webpage", {"job_id": job_id, "scraper": scraper_type})
            
            if use_simple_scraper:
                result = await simple_scrape(url, {"timeout": timeout / 1000})
            else:
                result = await firecrawl_scrape(url, {"timeout": timeout, "wait_for": wait_for, "formats": ["html", "markdown"]})
            
            if not result.get("success"):
                await emit_failure(context, job_id, f"Scraping failed: {result.get('error', 'Unknown')}", "fetching", url)
                return
            
            markdown = result.get("markdown") or to_markdown(result.get("html", ""))
            metadata = result.get("metadata", {})
            
            if not markdown or not markdown.strip():
                await emit_failure(context, job_id, "Empty content after conversion", "fetching", url)
                return
            
            # Cache content for future use
            try:
                from datetime import datetime, timezone
                await context.state.set("content_cache", url_hash, {
                    "markdown": markdown,
                    "url": url,
                    "cached_at": datetime.now(timezone.utc).isoformat(),
                    "metadata": metadata
                })
            except Exception:
                pass
        
        # 7. Store markdown in state (avoids 4KB event limit)
        await context.state.set("fetch_payloads", job_id, {
            "markdown": markdown,
            "schema": schema,
            "metadata": metadata
        })
        
        # 8. Emit minimal payload for LLM extraction
        await update_progress(context.streams, job_id, "fetched", 40, "Content fetched, extracting...")
        
        await context.emit({
            "topic": "webpage.fetched",
            "data": {
                "job_id": job_id,
                "url": url,
                "scraper_id": scraper_id,
                "options": options,
                "cached": content_cached,
                "cache_type": "content" if content_cached else None,
                "markdown_length": len(markdown)
            }
        })
        
        context.logger.info("Fetch completed", {
            "job_id": job_id,
            "content_cached": content_cached,
            "markdown_length": len(markdown)
        })
        
    except Exception as e:
        context.logger.error("Fetch failed", {"job_id": job_id, "error": str(e)})
        await emit_failure(context, job_id, f"Unexpected error: {str(e)}", "fetching", url)


async def emit_failure(context, job_id: str, error: str, stage: str, url: str = None) -> None:
    """Emit extraction.failed event."""
    context.logger.error(f"Fetch failed: {error}", {"job_id": job_id, "stage": stage})
    await context.emit({
        "topic": "extraction.failed",
        "data": {
            "job_id": job_id,
            "error": error,
            "stage": stage,
            "url": url
        }
    })
