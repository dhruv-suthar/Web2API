from typing import Dict, Any

# Response schema for 200 OK
response_schema = {
    200: {
        "type": "object",
        "properties": {
            "scrapers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "scraper_id": {
                            "type": "string",
                            "description": "Unique scraper identifier"
                        },
                        "name": {
                            "type": "string",
                            "description": "Human-readable name for this scraper"
                        },
                        "description": {
                            "type": "string",
                            "description": "What this scraper extracts"
                        },
                        "schema": {
                            "description": "The extraction schema"
                        },
                        "example_url": {
                            "type": "string",
                            "description": "Example URL this scraper is designed for"
                        },
                        "endpoint": {
                            "type": "string",
                            "description": "Full endpoint path: /api/scrape/{scraper_id}"
                        },
                        "created_at": {
                            "type": "string",
                            "format": "date-time",
                            "description": "When the scraper was created"
                        }
                    },
                    "required": ["scraper_id", "name", "endpoint", "created_at"]
                }
            },
            "count": {
                "type": "integer",
                "description": "Total number of scrapers"
            }
        },
        "required": ["scrapers", "count"]
    },
    500: {
        "type": "object",
        "properties": {
            "error": {
                "type": "string"
            }
        },
        "required": ["error"]
    }
}

config = {
    "name": "ListScrapers",
    "type": "api",
    "path": "/scrapers",
    "method": "GET",
    "description": "List all scrapers",
    "emits": [],
    "flows": ["scraper-management"],
    "queryParams": [
        {
            "name": "limit",
            "description": "Maximum number of scrapers to return (optional, for future pagination)"
        },
        {
            "name": "offset",
            "description": "Number of scrapers to skip (optional, for future pagination)"
        }
    ],
    "responseSchema": response_schema
}


def format_scraper_for_listing(scraper: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a scraper object for listing response.
    Returns only the essential fields needed for listing.
    
    Args:
        scraper: Full scraper configuration from state
    
    Returns:
        Formatted scraper object with essential fields
    """
    return {
        "scraper_id": scraper.get("scraper_id"),
        "name": scraper.get("name"),
        "description": scraper.get("description"),
        "schema": scraper.get("schema"),
        "example_url": scraper.get("example_url"),
        "endpoint": f"/api/scrape/{scraper.get('scraper_id')}",
        "created_at": scraper.get("created_at")
    }


async def handler(req: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handler for listing all scrapers.
    
    Args:
        req: Request dictionary containing:
            - pathParams: Path parameters (empty for this endpoint)
            - queryParams: Query parameters (limit, offset for future pagination)
            - body: Request body (empty for GET requests)
            - headers: Request headers
        context: Motia context containing:
            - state: State manager for retrieving scrapers
            - logger: Logger for structured logging
            - emit: Event emitter (not used in this step)
    
    Returns:
        Response dictionary with status and body containing list of scrapers
    """
    try:
        # Get all scrapers from state
        all_scrapers = await context.state.get_group("scrapers")
        
        # Store total count before pagination
        total_count = len(all_scrapers)
        
        # context.logger.info("Listing scrapers", {
        #     "total_count": total_count
        # })
        
        # Format scrapers for response (exclude full schema and internal fields)
        formatted_scrapers = [
            format_scraper_for_listing(scraper)
            for scraper in all_scrapers
        ]
        
        # Sort by created_at (newest first) if available
        formatted_scrapers.sort(
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )
        
        # Handle pagination query parameters (for future use)
        query_params = req.get("queryParams", {})
        limit = query_params.get("limit")
        offset = query_params.get("offset")
        
        # Apply pagination if provided
        if offset:
            try:
                offset_int = int(offset) if isinstance(offset, str) else offset
                formatted_scrapers = formatted_scrapers[offset_int:]
            except (ValueError, TypeError):
                context.logger.warn("Invalid offset parameter, ignoring", {
                    "offset": offset
                })
        
        if limit:
            try:
                limit_int = int(limit) if isinstance(limit, str) else limit
                formatted_scrapers = formatted_scrapers[:limit_int]
            except (ValueError, TypeError):
                context.logger.warn("Invalid limit parameter, ignoring", {
                    "limit": limit
                })
        
        # Return response with total count and paginated results
        return {
            "status": 200,
            "body": {
                "scrapers": formatted_scrapers,
                "count": total_count
            }
        }
        
    except Exception as e:
        # context.logger.error("Failed to list scrapers - unexpected error", {
        #     "error": str(e),
        #     "error_type": type(e).__name__
        # })
        return {
            "status": 500,
            "body": {
                "error": "Failed to list scrapers"
            }
        }

