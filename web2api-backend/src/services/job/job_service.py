"""
Job Service

Business logic for job lifecycle management.
Handles job creation, status updates, and polling.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from src.utils.hash_utils import generate_job_id


def create_job_metadata(
    job_id: str,
    scraper_id: str,
    url: str,
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create job metadata object.
    
    Args:
        job_id: Unique job identifier
        scraper_id: Scraper being used
        url: Target URL
        options: Merged scraping options
        
    Returns:
        Job metadata dictionary
    """
    return {
        "job_id": job_id,
        "scraper_id": scraper_id,
        "url": url,
        "status": "queued",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "options": options
    }


async def update_job_status(
    state,
    job_id: str,
    status: str,
    **extra_fields
) -> None:
    """
    Update job status in state.
    
    Args:
        state: Motia state object
        job_id: Job identifier
        status: New status
        **extra_fields: Additional fields to update
    """
    try:
        job_result = await state.get("jobs", job_id)
        if job_result:
            job = job_result.get("data", job_result) if isinstance(job_result, dict) else job_result
            if job:
                job["status"] = status
                job["updated_at"] = datetime.now(timezone.utc).isoformat()
                job.update(extra_fields)
                await state.set("jobs", job_id, job)
    except Exception:
        pass


async def poll_for_completion(
    state,
    job_id: str,
    timeout_seconds: int = 30,
    poll_interval: float = 0.5
) -> Optional[Dict[str, Any]]:
    """
    Poll state for job completion in sync mode.
    
    Args:
        state: Motia state object
        job_id: Job ID to poll for
        timeout_seconds: Maximum time to wait (default 30s)
        poll_interval: Time between polls in seconds (default 0.5s)
    
    Returns:
        Extraction result dict if completed, None if timeout or failed
    """
    start_time = datetime.now(timezone.utc)
    
    while True:
        # Check timeout
        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        if elapsed >= timeout_seconds:
            return None
        
        # Check job status
        job_result = await state.get("jobs", job_id)
        if job_result:
            job = job_result.get("data", job_result) if isinstance(job_result, dict) else job_result
            status = job.get("status") if job else None
            
            if status == "completed":
                extraction_result = await state.get("extractions", job_id)
                if extraction_result:
                    extraction = extraction_result.get("data", extraction_result) if isinstance(extraction_result, dict) else extraction_result
                    if extraction:
                        return extraction
            
            if status == "failed":
                return {
                    "job_id": job_id,
                    "status": "failed",
                    "error": job.get("error", "Extraction failed")
                }
        
        # Wait before next poll
        await asyncio.sleep(poll_interval)
    
    return None

