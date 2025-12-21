"""
Run Scraper API Step

The main endpoint developers use to execute a pre-configured scraper against a URL.
Follows DDD principles: thin controller that delegates to services.

Optimized for Motia Cloud:
- Event payloads kept under 4KB limit
- Large data (schema) stored in state for event steps
- Cache checked BEFORE emitting events for instant cache hits
"""

from typing import Dict, Any

# Import services - paths relative to project root for Motia bundling
from src.utils.hash_utils import generate_job_id
from src.utils.state_utils import unwrap_state_data
from src.services.job.job_service import create_job_metadata, poll_for_completion
from src.services.monitoring.monitor_service import auto_add_to_monitoring
from src.services.cache.cache_service import get_cached_extraction


# Request body schema
body_schema = {
    "type": "object",
    "properties": {
        "url": {
            "type": "string",
            "description": "Target URL to scrape using this scraper's schema"
        },
        "options": {
            "type": "object",
            "properties": {
                "use_cache": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to use cached content if available"
                },
                "wait_for": {
                    "type": "integer",
                    "default": 2000,
                    "description": "Wait time in ms for JS to render"
                },
                "async": {
                    "type": "boolean",
                    "default": False,
                    "description": "If true, return job_id immediately"
                },
                "skip_monitoring": {
                    "type": "boolean",
                    "default": False,
                    "description": "If true, don't add this URL to scheduled monitoring"
                }
            }
        }
    },
    "required": ["url"]
}

# Response schemas
response_schema = {
    200: {
        "type": "object",
        "properties": {
            "job_id": {"type": "string"},
            "scraper_id": {"type": "string"},
            "status": {"type": "string", "enum": ["completed", "failed"]},
            "data": {"type": "object"},
            "url": {"type": "string"},
            "cached": {"type": "boolean"},
            "monitoring": {"type": "boolean"},
            "monitor_id": {"type": "string"},
            "next_run": {"type": "string", "format": "date-time"}
        },
        "required": ["job_id", "scraper_id", "status", "url"]
    },
    202: {
        "type": "object",
        "properties": {
            "job_id": {"type": "string"},
            "scraper_id": {"type": "string"},
            "status": {"type": "string", "enum": ["queued"]},
            "status_url": {"type": "string"},
            "results_url": {"type": "string"},
            "monitoring": {"type": "boolean"},
            "monitor_id": {"type": "string"},
            "next_run": {"type": "string", "format": "date-time"}
        },
        "required": ["job_id", "scraper_id", "status", "status_url", "results_url"]
    },
    400: {"type": "object", "properties": {"error": {"type": "string"}}, "required": ["error"]},
    404: {"type": "object", "properties": {"error": {"type": "string"}}, "required": ["error"]},
    500: {"type": "object", "properties": {"error": {"type": "string"}}, "required": ["error"]}
}

config = {
    "name": "RunScraper",
    "type": "api",
    "path": "/scrape/:scraperId",
    "method": "POST",
    "description": "Execute a pre-configured scraper against a URL",
    "emits": ["extraction.requested"],
    "flows": ["extraction-flow"],
    "bodySchema": body_schema,
    "responseSchema": response_schema,
    # Include service/util dependencies for Motia Cloud deployment
    # Paths are relative from steps/api/ to src/
    "includeFiles": [
        "../../src/utils/__init__.py",
        "../../src/utils/hash_utils.py",
        "../../src/utils/state_utils.py",
        "../../src/services/__init__.py",
        "../../src/services/job/__init__.py",
        "../../src/services/job/job_service.py",
        "../../src/services/monitoring/__init__.py",
        "../../src/services/monitoring/monitor_service.py",
        "../../src/services/cache/__init__.py",
        "../../src/services/cache/cache_service.py",
    ]
}


async def handler(req: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handler for running a scraper - thin controller pattern.
    Stores large data in state to comply with 4KB event payload limit.
    """
    try:
        # 1. Extract and validate input
        scraper_id = req.get("pathParams", {}).get("scraperId")
        if not scraper_id:
            return {"status": 400, "body": {"error": "Scraper ID is required in path"}}
        
        body = req.get("body", {})
        url = body.get("url", "").strip()
        if not url:
            return {"status": 400, "body": {"error": "url is required"}}
        
        options = body.get("options", {})
        is_async = options.get("async", False)
        skip_monitoring = options.get("skip_monitoring", False)
        
        # 2. Get scraper from state
        scraper_result = await context.state.get("scrapers", scraper_id)
        scraper = unwrap_state_data(scraper_result)
        
        if not scraper:
            return {"status": 404, "body": {"error": f"Scraper '{scraper_id}' not found"}}
        
        # 3. Create job
        job_id = generate_job_id()
        scraper_options = scraper.get("options", {})
        merged_options = {
            "use_cache": options.get("use_cache", True),
            "wait_for": options.get("wait_for", scraper_options.get("wait_for", 2000)),
            "timeout": options.get("timeout", scraper_options.get("timeout", 30000)),
            "use_simple_scraper": options.get("use_simple_scraper", scraper_options.get("use_simple_scraper", False))
        }
        
        job_metadata = create_job_metadata(job_id, scraper_id, url, merged_options)
        await context.state.set("jobs", job_id, job_metadata)
        
        # 4. Get schema for cache check
        schema = scraper.get("schema")
        use_cache = merged_options.get("use_cache", True)
        
        # 5. CHECK CACHE FIRST - instant response for cache hits (no events, no polling)
        if use_cache and not is_async:
            cached_extraction = await get_cached_extraction(context.state, url, schema)
            
            if cached_extraction:
                context.logger.info("Cache hit in API - instant response", {
                    "job_id": job_id, 
                    "scraper_id": scraper_id, 
                    "url": url,
                    "cached_at": cached_extraction.get("cached_at")
                })
                
                # Handle monitoring
                monitor_info = {"monitoring": False, "monitor_id": None, "next_run": None}
                schedule_info = scraper.get("schedule_info")
                if schedule_info and not skip_monitoring:
                    monitor_info = await auto_add_to_monitoring(
                        context.state, scraper_id, url, schedule_info
                    )
                
                return {
                    "status": 200,
                    "body": {
                        "job_id": job_id,
                        "scraper_id": scraper_id,
                        "status": "completed",
                        "data": cached_extraction.get("data", {}),
                        "url": url,
                        "cached": True,
                        "cache_type": "extraction",
                        "cached_at": cached_extraction.get("cached_at"),
                        "monitoring": monitor_info.get("monitoring", False),
                        "monitor_id": monitor_info.get("monitor_id"),
                        "next_run": monitor_info.get("next_run")
                    }
                }
        
        # 6. Store schema in state for event steps (avoids 4KB event limit)
        await context.state.set("job_payloads", job_id, {
            "schema": schema,
            "scraper_id": scraper_id
        })
        
        context.logger.info("Job created - cache miss, processing", {"job_id": job_id, "scraper_id": scraper_id, "url": url})
        
        # 7. Emit minimal extraction event
        # NOTE: We use job_id as messageGroupId instead of url hash to avoid FIFO queue blocking.
        # Using url hash caused subsequent requests for the same URL to block while previous
        # messages were "in flight" due to FIFO deduplication/ordering guarantees.
        # Each job should be processed independently.
        await context.emit({
            "topic": "extraction.requested",
            "data": {
                "job_id": job_id,
                "url": url,
                "scraper_id": scraper_id,
                "options": merged_options
            },
            "messageGroupId": job_id
        })
        
        # 8. Handle monitoring (service call)
        monitor_info = {"monitoring": False, "monitor_id": None, "next_run": None}
        schedule_info = scraper.get("schedule_info")
        
        if schedule_info and not skip_monitoring:
            monitor_info = await auto_add_to_monitoring(
                context.state, scraper_id, url, schedule_info
            )
        
        # 9. Build response based on sync/async mode
        if is_async:
            return {
                "status": 202,
                "body": {
                    "job_id": job_id,
                    "scraper_id": scraper_id,
                    "status": "queued",
                    "status_url": f"/api/status/{job_id}",
                    "results_url": f"/api/results/{job_id}",
                    "monitoring": monitor_info.get("monitoring", False),
                    "monitor_id": monitor_info.get("monitor_id"),
                    "next_run": monitor_info.get("next_run")
                }
            }
        
        # Sync mode: poll for completion
        result = await poll_for_completion(context.state, job_id, timeout_seconds=30)
        
        if result and result.get("status") == "completed":
            return {
                "status": 200,
                "body": {
                    "job_id": job_id,
                    "scraper_id": scraper_id,
                    "status": "completed",
                    "data": result.get("data", {}),
                    "url": url,
                    "cached": result.get("cached", False),
                    "monitoring": monitor_info.get("monitoring", False),
                    "monitor_id": monitor_info.get("monitor_id"),
                    "next_run": monitor_info.get("next_run")
                }
            }
        
        if result and result.get("status") == "failed":
            return {
                "status": 200,
                "body": {
                    "job_id": job_id,
                    "scraper_id": scraper_id,
                    "status": "failed",
                    "error": result.get("error", "Extraction failed"),
                    "url": url,
                    "monitoring": monitor_info.get("monitoring", False)
                }
            }
        
        # Timeout - return async-style response
        return {
            "status": 202,
            "body": {
                "job_id": job_id,
                "scraper_id": scraper_id,
                "status": "queued",
                "message": "Request timed out, processing continues in background",
                "status_url": f"/api/status/{job_id}",
                "results_url": f"/api/results/{job_id}",
                "monitoring": monitor_info.get("monitoring", False)
            }
        }
        
    except Exception as e:
        context.logger.error("Run scraper failed", {"error": str(e)})
        return {"status": 500, "body": {"error": "Internal server error"}}
