"""
Create Scraper API Step

Create a new scraper configuration with extraction schema.
Follows DDD principles: thin controller that delegates to services.
"""

from datetime import datetime, timezone
from typing import Dict, Any

# Import services - paths relative to project root for Motia bundling
from src.utils.hash_utils import generate_scraper_id
from src.services.monitoring.monitor_service import parse_schedule, create_monitors_for_urls


# Request body schema
body_schema = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "minLength": 1,
            "description": "Human-readable name for this scraper"
        },
        "description": {
            "type": "string",
            "description": "What this scraper extracts"
        },
        "schema": {
            "oneOf": [
                {"type": "string", "description": "Natural language prompt"},
                {"type": "object", "description": "JSON Schema"}
            ]
        },
        "example_url": {
            "type": "string",
            "description": "Example URL for documentation"
        },
        "webhook_url": {
            "type": "string",
            "description": "Default webhook URL for extractions"
        },
        "schedule": {
            "oneOf": [
                {"type": "string", "description": "Cron expression (e.g., '0 */1 * * *' for hourly)"},
                {"type": "integer", "minimum": 5, "description": "Interval in minutes (minimum 5)"}
            ],
            "description": "Auto re-scrape monitored URLs on this schedule. Minimum interval: 5 minutes."
        },
        "monitor_urls": {
            "type": "array",
            "items": {"type": "string"},
            "description": "URLs to automatically monitor on schedule"
        },
        "options": {
            "type": "object",
            "properties": {
                "timeout": {"type": "integer", "default": 30000},
                "use_simple_scraper": {"type": "boolean", "default": False},
                "wait_for": {"type": "integer", "default": 2000}
            }
        }
    },
    "required": ["name", "schema"]
}

# Response schema
response_schema = {
    201: {
        "type": "object",
        "properties": {
            "scraper_id": {"type": "string"},
            "name": {"type": "string"},
            "description": {"type": "string"},
            "endpoint": {"type": "string"},
            "schema": {},
            "schedule": {},
            "monitors_created": {"type": "integer"},
            "created_at": {"type": "string", "format": "date-time"}
        },
        "required": ["scraper_id", "name", "endpoint", "schema", "created_at"]
    },
    400: {"type": "object", "properties": {"error": {"type": "string"}}, "required": ["error"]},
    500: {"type": "object", "properties": {"error": {"type": "string"}}, "required": ["error"]}
}

config = {
    "name": "CreateScraper",
    "type": "api",
    "path": "/scrapers",
    "method": "POST",
    "description": "Create a new scraper configuration with extraction schema",
    "emits": [],
    "flows": ["scraper-management"],
    "bodySchema": body_schema,
    "responseSchema": response_schema,
    # Include service/util dependencies for Motia Cloud deployment
    # Paths are relative from steps/api/ to src/
    "includeFiles": [
        "../../src/utils/__init__.py",
        "../../src/utils/hash_utils.py",
        "../../src/services/__init__.py",
        "../../src/services/monitoring/__init__.py",
        "../../src/services/monitoring/monitor_service.py",
    ]
}


async def handler(req: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handler for creating a new scraper - thin controller pattern.
    """
    try:
        body = req.get("body", {})
        
        # 1. Validate required fields
        name = body.get("name", "").strip()
        schema = body.get("schema")
        
        if not name:
            return {"status": 400, "body": {"error": "name is required"}}
        
        if schema is None:
            return {"status": 400, "body": {"error": "schema is required"}}
        
        if not isinstance(schema, (str, dict)):
            return {"status": 400, "body": {"error": "schema must be string or object"}}
        
        # 2. Generate ID and timestamp
        scraper_id = generate_scraper_id()
        created_at = datetime.now(timezone.utc).isoformat()
        
        # 3. Parse and validate schedule (minimum 5 minutes)
        schedule = body.get("schedule")
        schedule_info = None
        
        if schedule is not None:
            if isinstance(schedule, int):
                if schedule < 5:
                    return {"status": 400, "body": {"error": "schedule must be at least 5 minutes"}}
                schedule_info = parse_schedule(schedule)
            elif isinstance(schedule, str):
                schedule_info = parse_schedule(schedule)
            else:
                return {"status": 400, "body": {"error": "schedule must be integer (minutes) or cron string"}}
        
        monitor_urls = body.get("monitor_urls", [])
        options = body.get("options", {})
        
        # 4. Build scraper config
        scraper_config = {
            "scraper_id": scraper_id,
            "name": name,
            "description": body.get("description"),
            "schema": schema,
            "example_url": body.get("example_url"),
            "webhook_url": body.get("webhook_url"),
            "schedule": schedule,
            "schedule_info": schedule_info,
            "options": {
                "timeout": options.get("timeout", 30000),
                "use_simple_scraper": options.get("use_simple_scraper", False),
                "wait_for": options.get("wait_for", 2000)
            },
            "created_at": created_at
        }
        
        # 5. Store scraper
        await context.state.set("scrapers", scraper_id, scraper_config)
        
        # 6. Create monitors for URLs (service call)
        monitors_created = 0
        if schedule_info and monitor_urls:
            monitors_created = await create_monitors_for_urls(
                context.state, scraper_id, monitor_urls, schedule_info
            )
        
        context.logger.info("Scraper created", {
            "scraper_id": scraper_id,
            "name": name,
            "monitors_created": monitors_created
        })
        
        # 7. Build response
        response = {
            "scraper_id": scraper_id,
            "name": name,
            "description": scraper_config["description"],
            "endpoint": f"/api/scrape/{scraper_id}",
            "schema": schema,
            "created_at": created_at
        }
        
        if schedule:
            response["schedule"] = schedule
        if monitors_created > 0:
            response["monitors_created"] = monitors_created
        
        return {"status": 201, "body": response}
        
    except Exception as e:
        context.logger.error("Create scraper failed", {"error": str(e)})
        return {"status": 500, "body": {"error": "Failed to create scraper"}}

