"""
Progress Service

Handles job progress updates via streams.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


async def update_progress(
    streams,
    job_id: str,
    status: str,
    percent: int,
    message: Optional[str] = None
) -> None:
    """
    Update job progress in stream.
    
    Args:
        streams: Motia streams object
        job_id: Job identifier
        status: Status string (e.g., "fetching", "extracting")
        percent: Progress percentage (0-100)
        message: Optional progress message
    """
    try:
        if hasattr(streams, 'jobProgress'):
            progress_data = {
                "id": job_id,
                "status": status,
                "percent": percent,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            if message:
                progress_data["message"] = message
            
            await streams.jobProgress.set(job_id, job_id, progress_data)
    except Exception as e:
        # Don't fail if stream update fails
        logger.debug(f"Failed to update progress: {e}")

