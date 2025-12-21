"""
Run Scheduled Monitors Cron Step

Checks for due monitors and triggers fresh scrapes.
Runs every 5 minutes to check for due monitors.

Optimized for Motia Cloud:
- Event payloads kept under 4KB limit
- Large data (schema) stored in state for event steps
"""

from datetime import datetime, timezone
from typing import Dict, Any

# Import services - paths relative to project root for Motia bundling
from src.utils.hash_utils import generate_job_id, hash_url
from src.services.monitoring.monitor_service import calculate_next_run
from src.services.job.job_service import create_job_metadata


config = {
    "name": "RunScheduledMonitors",
    "type": "cron",
    "cron": "*/5 * * * *",
    "description": "Check and trigger due scheduled monitors",
    "emits": ["extraction.requested"],
    "flows": ["scheduled-scraping"],
    # Include service/util dependencies for Motia Cloud deployment
    # Paths are relative from steps/cron/ to src/
    "includeFiles": [
        "../../src/utils/__init__.py",
        "../../src/utils/hash_utils.py",
        "../../src/services/__init__.py",
        "../../src/services/monitoring/__init__.py",
        "../../src/services/monitoring/monitor_service.py",
        "../../src/services/job/__init__.py",
        "../../src/services/job/job_service.py",
    ]
}


def parse_datetime(dt_str: str) -> datetime:
    """Parse ISO datetime string."""
    try:
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return None


async def handler(context) -> None:
    """
    Cron handler for scheduled monitors - thin controller pattern.
    Stores large data in state to comply with 4KB event payload limit.
    """
    now = datetime.now(timezone.utc)
    context.logger.info("Checking scheduled monitors", {"check_time": now.isoformat()})
    
    try:
        # 1. Get all monitors
        monitors_result = await context.state.get_group("monitors")
        
        if not monitors_result:
            context.logger.info("No monitors found")
            return
        
        # Handle response format
        if isinstance(monitors_result, list):
            monitors = monitors_result
        elif isinstance(monitors_result, dict):
            monitors = monitors_result.get("data", [])
            if not isinstance(monitors, list):
                monitors = list(monitors_result.values())
        else:
            monitors = []
        
        if not monitors:
            context.logger.info("No monitors found")
            return
        
        context.logger.info("Found monitors", {"count": len(monitors)})
        
        # 2. Process each monitor
        triggered = 0
        skipped = 0
        
        for monitor in monitors:
            if not isinstance(monitor, dict):
                continue
            
            if not monitor.get("active", False):
                skipped += 1
                continue
            
            monitor_id = monitor.get("monitor_id")
            scraper_id = monitor.get("scraper_id")
            url = monitor.get("url")
            next_run_str = monitor.get("next_run")
            
            if not all([monitor_id, scraper_id, url, next_run_str]):
                continue
            
            # Check if due
            next_run = parse_datetime(next_run_str)
            if not next_run or next_run > now:
                skipped += 1
                continue
            
            # Get scraper
            scraper_result = await context.state.get("scrapers", scraper_id)
            if not scraper_result:
                context.logger.warn("Scraper not found", {"scraper_id": scraper_id})
                continue
            
            scraper = scraper_result.get("data", scraper_result) if isinstance(scraper_result, dict) else scraper_result
            if not scraper:
                continue
            
            # Generate job
            job_id = generate_job_id()
            url_group_id = hash_url(url)
            
            merged_options = {
                "use_cache": False,
                **scraper.get("options", {})
            }
            
            # Store job metadata
            job_metadata = create_job_metadata(job_id, scraper_id, url, merged_options)
            await context.state.set("jobs", job_id, job_metadata)
            
            # Store schema in state for event steps (avoids 4KB event limit)
            schema = scraper.get("schema")
            await context.state.set("job_payloads", job_id, {
                "schema": schema,
                "scraper_id": scraper_id
            })
            
            # Emit minimal payload with FIFO messageGroupId
            await context.emit({
                "topic": "extraction.requested",
                "data": {
                    "job_id": job_id,
                    "url": url,
                    "scraper_id": scraper_id,
                    "options": merged_options
                },
                "messageGroupId": url_group_id
            })
            
            # Update monitor
            schedule_info = scraper.get("schedule_info") or {
                "type": monitor.get("schedule_type", "interval"),
                "interval_minutes": monitor.get("interval_minutes"),
                "cron": monitor.get("cron")
            }
            
            monitor["last_run"] = now.isoformat()
            monitor["next_run"] = calculate_next_run(schedule_info)
            monitor["run_count"] = monitor.get("run_count", 0) + 1
            monitor["last_job_id"] = job_id
            
            await context.state.set("monitors", monitor_id, monitor)
            
            triggered += 1
            context.logger.info("Triggered monitor", {"monitor_id": monitor_id, "job_id": job_id})
        
        context.logger.info("Check completed", {"triggered": triggered, "skipped": skipped})
        
    except Exception as e:
        context.logger.error("Cron check failed", {"error": str(e)})
