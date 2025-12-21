"""
List Monitors API Step

GET /monitors - List all scheduled monitors
GET /monitors?scraper_id=scr_xxx - Filter by scraper ID

Returns list of active monitors with their schedule information,
next run time, and run statistics.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# Response schema for 200 OK
response_schema_200 = {
    "type": "object",
    "properties": {
        "monitors": {
            "type": "array",
            "description": "List of scheduled monitors",
            "items": {
                "type": "object",
                "properties": {
                    "monitor_id": {
                        "type": "string",
                        "description": "Unique monitor identifier"
                    },
                    "scraper_id": {
                        "type": "string",
                        "description": "Associated scraper ID"
                    },
                    "url": {
                        "type": "string",
                        "description": "URL being monitored"
                    },
                    "schedule_type": {
                        "type": "string",
                        "enum": ["interval", "cron"],
                        "description": "Type of schedule"
                    },
                    "interval_minutes": {
                        "type": "integer",
                        "description": "Interval in minutes (if schedule_type is interval)"
                    },
                    "interval_hours": {
                        "type": "integer",
                        "description": "Interval in hours (legacy, if schedule_type is interval)"
                    },
                    "cron": {
                        "type": "string",
                        "description": "Cron expression (if schedule_type is cron)"
                    },
                    "active": {
                        "type": "boolean",
                        "description": "Whether monitor is active"
                    },
                    "last_run": {
                        "type": "string",
                        "format": "date-time",
                        "description": "Last run timestamp"
                    },
                    "next_run": {
                        "type": "string",
                        "format": "date-time",
                        "description": "Next scheduled run timestamp"
                    },
                    "run_count": {
                        "type": "integer",
                        "description": "Total number of scheduled runs"
                    },
                    "last_job_id": {
                        "type": "string",
                        "description": "Job ID of last scheduled run"
                    },
                    "created_at": {
                        "type": "string",
                        "format": "date-time"
                    },
                    "updated_at": {
                        "type": "string",
                        "format": "date-time"
                    }
                },
                "required": ["monitor_id", "scraper_id", "url", "active"]
            }
        },
        "total": {
            "type": "integer",
            "description": "Total number of monitors"
        },
        "active_count": {
            "type": "integer",
            "description": "Number of active monitors"
        }
    },
    "required": ["monitors", "total"]
}

# Response schema for errors
response_schema_error = {
    "type": "object",
    "properties": {
        "error": {
            "type": "string"
        }
    },
    "required": ["error"]
}

# API step configuration
config = {
    "name": "ListMonitors",
    "type": "api",
    "path": "/monitors",
    "method": "GET",
    "description": "List all scheduled monitors, optionally filtered by scraper_id",
    "emits": [],
    "flows": ["scheduled-scraping"],
    "queryParams": [
        {
            "name": "scraper_id",
            "description": "Filter monitors by scraper ID"
        },
        {
            "name": "active_only",
            "description": "If 'true', only return active monitors (default: false)"
        }
    ],
    "responseSchema": {
        200: response_schema_200,
        500: response_schema_error
    }
}


async def handler(req: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handler for listing scheduled monitors.
    
    Args:
        req: Request dictionary containing:
            - queryParams: Optional filter parameters
                - scraper_id: Filter by scraper ID
                - active_only: If 'true', only return active monitors
        context: Motia context containing:
            - state: State manager for retrieving monitors
            - logger: Logger for structured logging
    
    Returns:
        Response dictionary with list of monitors
    """
    try:
        # Get query parameters
        query_params = req.get("queryParams", {})
        scraper_id_filter = query_params.get("scraper_id")
        active_only = query_params.get("active_only", "").lower() == "true"
        
        # Handle array values (some frameworks pass query params as arrays)
        if isinstance(scraper_id_filter, list):
            scraper_id_filter = scraper_id_filter[0] if scraper_id_filter else None
        
        context.logger.info("Listing monitors", {
            "scraper_id_filter": scraper_id_filter,
            "active_only": active_only
        })
        
        # Get all monitors from state
        try:
            monitors_result = await context.state.get_group("monitors")
            
            # Handle different response formats
            if monitors_result is None:
                monitors = []
            elif isinstance(monitors_result, list):
                monitors = monitors_result
            elif isinstance(monitors_result, dict):
                # Might be wrapped in {"data": [...]}
                data = monitors_result.get("data")
                if isinstance(data, list):
                    monitors = data
                elif isinstance(data, dict):
                    monitors = list(data.values())
                else:
                    monitors = list(monitors_result.values()) if monitors_result else []
            else:
                monitors = []
                
        except Exception as e:
            context.logger.error("Failed to get monitors from state", {
                "error": str(e),
                "error_type": type(e).__name__
            })
            return {
                "status": 500,
                "body": {
                    "error": "Failed to retrieve monitors"
                }
            }
        
        # Filter monitors
        filtered_monitors = []
        active_count = 0
        
        for monitor in monitors:
            if not isinstance(monitor, dict):
                continue
            
            # Track active count
            is_active = monitor.get("active", False)
            if is_active:
                active_count += 1
            
            # Apply filters
            if scraper_id_filter and monitor.get("scraper_id") != scraper_id_filter:
                continue
            
            if active_only and not is_active:
                continue
            
            # Format monitor for response
            formatted_monitor = {
                "monitor_id": monitor.get("monitor_id"),
                "scraper_id": monitor.get("scraper_id"),
                "url": monitor.get("url"),
                "schedule_type": monitor.get("schedule_type"),
                "interval_minutes": monitor.get("interval_minutes"),
                "interval_hours": monitor.get("interval_hours"),  # Legacy support
                "cron": monitor.get("cron"),
                "active": is_active,
                "last_run": monitor.get("last_run"),
                "next_run": monitor.get("next_run"),
                "run_count": monitor.get("run_count", 0),
                "last_job_id": monitor.get("last_job_id"),
                "created_at": monitor.get("created_at"),
                "updated_at": monitor.get("updated_at")
            }
            
            # Remove None values for cleaner response
            formatted_monitor = {k: v for k, v in formatted_monitor.items() if v is not None}
            
            filtered_monitors.append(formatted_monitor)
        
        # Sort by created_at (newest first)
        filtered_monitors.sort(
            key=lambda m: m.get("created_at", ""),
            reverse=True
        )
        
        context.logger.info("Monitors listed", {
            "total": len(monitors),
            "filtered": len(filtered_monitors),
            "active_count": active_count
        })
        
        return {
            "status": 200,
            "body": {
                "monitors": filtered_monitors,
                "total": len(filtered_monitors),
                "active_count": active_count
            }
        }
        
    except Exception as e:
        context.logger.error("List monitors failed", {
            "error": str(e),
            "error_type": type(e).__name__
        })
        
        return {
            "status": 500,
            "body": {
                "error": "Failed to list monitors"
            }
        }

