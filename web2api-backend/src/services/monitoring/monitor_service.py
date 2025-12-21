"""
Monitor Service

Business logic for scheduled monitoring of scrapers.
Handles schedule parsing, next run calculation, and monitor lifecycle.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Union, List

from src.utils.hash_utils import generate_monitor_id


def parse_schedule(schedule: Union[str, int, None]) -> Optional[Dict[str, Any]]:
    """
    Parse schedule option into a structured format.
    
    Args:
        schedule: Either:
            - string: Cron expression (e.g., "0 0 * * *")
            - int: Interval in minutes (e.g., 60 for hourly)
            - None: No schedule
            
    Returns:
        Dictionary with schedule info or None
        {
            "type": "cron" | "interval",
            "cron": str | None,
            "interval_minutes": int | None
        }
    """
    if schedule is None:
        return None
    
    if isinstance(schedule, int):
        return {
            "type": "interval",
            "cron": None,
            "interval_minutes": schedule
        }
    
    if isinstance(schedule, str):
        return {
            "type": "cron",
            "cron": schedule,
            "interval_minutes": None
        }
    
    return None


def calculate_next_run(schedule_info: Dict[str, Any]) -> str:
    """
    Calculate the next run time based on schedule info.
    
    Args:
        schedule_info: Parsed schedule dictionary
        
    Returns:
        ISO format datetime string for next run
    """
    now = datetime.now(timezone.utc)
    
    if schedule_info.get("type") == "interval":
        interval_minutes = schedule_info.get("interval_minutes", 60)
        next_run = now + timedelta(minutes=interval_minutes)
        return next_run.isoformat()
    
    if schedule_info.get("type") == "cron":
        try:
            from croniter import croniter
            cron = croniter(schedule_info.get("cron"), now)
            next_run = cron.get_next(datetime)
            return next_run.isoformat()
        except ImportError:
            # Fall back to 60 minutes if croniter not available
            next_run = now + timedelta(minutes=60)
            return next_run.isoformat()
        except Exception:
            next_run = now + timedelta(minutes=60)
            return next_run.isoformat()
    
    # Default to 60 minutes
    next_run = now + timedelta(minutes=60)
    return next_run.isoformat()


def create_monitor(
    scraper_id: str,
    url: str,
    schedule_info: Dict[str, Any],
    existing_monitor: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a monitor data object.
    
    Args:
        scraper_id: Scraper identifier
        url: URL to monitor
        schedule_info: Parsed schedule info
        existing_monitor: Existing monitor if updating
        
    Returns:
        Monitor data dictionary
    """
    now = datetime.now(timezone.utc)
    monitor_id = generate_monitor_id(scraper_id, url)
    next_run = calculate_next_run(schedule_info)
    
    return {
        "monitor_id": monitor_id,
        "scraper_id": scraper_id,
        "url": url,
        "interval_minutes": schedule_info.get("interval_minutes"),
        "cron": schedule_info.get("cron"),
        "schedule_type": schedule_info.get("type"),
        "active": True,
        "last_run": now.isoformat() if existing_monitor else None,
        "next_run": next_run,
        "run_count": existing_monitor.get("run_count", 0) if existing_monitor else 0,
        "last_job_id": None,
        "created_at": existing_monitor.get("created_at", now.isoformat()) if existing_monitor else now.isoformat(),
        "updated_at": now.isoformat()
    }


async def auto_add_to_monitoring(
    state,
    scraper_id: str,
    url: str,
    schedule_info: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Auto-add URL to monitoring if scraper has a schedule.
    
    Args:
        state: Motia state object
        scraper_id: Scraper identifier
        url: URL to monitor
        schedule_info: Parsed schedule info from scraper
        
    Returns:
        Dictionary with monitoring info:
        {
            "monitoring": bool,
            "monitor_id": str | None,
            "next_run": str | None,
            "action": "created" | "updated" | None
        }
    """
    if not schedule_info:
        return {
            "monitoring": False,
            "monitor_id": None,
            "next_run": None,
            "action": None
        }
    
    monitor_id = generate_monitor_id(scraper_id, url)
    
    # Check if monitor already exists
    existing_monitor = None
    try:
        existing_result = await state.get("monitors", monitor_id)
        if existing_result:
            existing_monitor = existing_result.get("data", existing_result) if isinstance(existing_result, dict) else existing_result
    except Exception:
        pass
    
    # Create monitor data
    monitor_data = create_monitor(scraper_id, url, schedule_info, existing_monitor)
    
    # Update last_run since we're running now
    monitor_data["last_run"] = datetime.now(timezone.utc).isoformat()
    
    # Save to state
    await state.set("monitors", monitor_id, monitor_data)
    
    return {
        "monitoring": True,
        "monitor_id": monitor_id,
        "next_run": monitor_data["next_run"],
        "action": "updated" if existing_monitor else "created"
    }


async def create_monitors_for_urls(
    state,
    scraper_id: str,
    urls: List[str],
    schedule_info: Dict[str, Any]
) -> int:
    """
    Create monitors for a list of URLs.
    
    Args:
        state: Motia state object
        scraper_id: Scraper identifier
        urls: List of URLs to monitor
        schedule_info: Parsed schedule info
        
    Returns:
        Number of monitors created
    """
    if not urls or not schedule_info:
        return 0
    
    monitors_created = 0
    
    for url in urls:
        if not url or not isinstance(url, str):
            continue
        
        url = url.strip()
        if not url:
            continue
        
        monitor_id = generate_monitor_id(scraper_id, url)
        monitor_data = create_monitor(scraper_id, url, schedule_info)
        
        try:
            await state.set("monitors", monitor_id, monitor_data)
            monitors_created += 1
        except Exception:
            pass
    
    return monitors_created

