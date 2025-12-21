"""
Delete Monitor API Step

DELETE /monitors/:monitorId - Stop and delete a scheduled monitor

This endpoint allows users to stop monitoring a specific URL by deleting
the monitor entry from state.
"""

from datetime import datetime, timezone
from typing import Dict, Any

from src.utils.state_utils import unwrap_state_data

# Response schema for 200 OK
response_schema_200 = {
    "type": "object",
    "properties": {
        "message": {
            "type": "string",
            "description": "Success message"
        },
        "monitor_id": {
            "type": "string",
            "description": "ID of the deleted monitor"
        },
        "deleted_at": {
            "type": "string",
            "format": "date-time",
            "description": "Deletion timestamp"
        }
    },
    "required": ["message", "monitor_id"]
}

# Response schema for 404 Not Found
response_schema_404 = {
    "type": "object",
    "properties": {
        "error": {
            "type": "string"
        }
    },
    "required": ["error"]
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
    "name": "DeleteMonitor",
    "type": "api",
    "path": "/monitors/:monitorId",
    "method": "DELETE",
    "description": "Stop and delete a scheduled monitor",
    "emits": [],
    "flows": ["scheduled-scraping"],
    "responseSchema": {
        200: response_schema_200,
        404: response_schema_404,
        500: response_schema_error
    },
    "includeFiles": [
        "../../src/utils/__init__.py",
        "../../src/utils/state_utils.py",
    ]
}


async def handler(req: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handler for deleting a scheduled monitor.
    
    Args:
        req: Request dictionary containing:
            - pathParams: Path parameters containing 'monitorId'
        context: Motia context containing:
            - state: State manager for deleting monitors
            - logger: Logger for structured logging
    
    Returns:
        Response dictionary with deletion confirmation or error
    """
    try:
        # Get monitor ID from path parameters
        path_params = req.get("pathParams", {})
        monitor_id = path_params.get("monitorId")
        
        if not monitor_id:
            return {
                "status": 400,
                "body": {
                    "error": "Monitor ID is required in path"
                }
            }
        
        context.logger.info("Deleting monitor", {"monitor_id": monitor_id})
        
        # Check if monitor exists
        try:
            monitor_result = await context.state.get("monitors", monitor_id)
            monitor = unwrap_state_data(monitor_result)
        except Exception as e:
            context.logger.error("Failed to get monitor", {
                "monitor_id": monitor_id,
                "error": str(e)
            })
            return {
                "status": 500,
                "body": {
                    "error": "Failed to retrieve monitor"
                }
            }
        
        if not monitor:
            return {
                "status": 404,
                "body": {
                    "error": f"Monitor with ID '{monitor_id}' not found"
                }
            }
        
        # Delete monitor from state
        try:
            await context.state.delete("monitors", monitor_id)
            
            deleted_at = datetime.now(timezone.utc).isoformat()
            
            context.logger.info("Monitor deleted", {
                "monitor_id": monitor_id,
                "scraper_id": monitor.get("scraper_id"),
                "url": monitor.get("url"),
                "deleted_at": deleted_at
            })
            
            return {
                "status": 200,
                "body": {
                    "message": f"Monitor '{monitor_id}' has been deleted",
                    "monitor_id": monitor_id,
                    "deleted_at": deleted_at
                }
            }
            
        except Exception as e:
            context.logger.error("Failed to delete monitor", {
                "monitor_id": monitor_id,
                "error": str(e)
            })
            return {
                "status": 500,
                "body": {
                    "error": "Failed to delete monitor"
                }
            }
        
    except Exception as e:
        context.logger.error("Delete monitor failed", {
            "error": str(e),
            "error_type": type(e).__name__
        })
        
        return {
            "status": 500,
            "body": {
                "error": "Failed to delete monitor"
            }
        }

