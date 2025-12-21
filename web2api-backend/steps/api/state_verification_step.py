"""
State Verification API Step

Tests all state groups used by the Web2API application:
- scrapers: Scraper configurations
- jobs: Job metadata
- extractions: Extraction results
- content_cache: Cached markdown content
- monitors: Scheduled monitoring configurations

This endpoint provides a way to verify that Motia's state management
is functioning correctly for all required state groups.

GET /debug/state-test - Run comprehensive state verification tests
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List

# Response schema for 200 OK
response_schema = {
    200: {
        "type": "object",
        "properties": {
            "success": {
                "type": "boolean",
                "description": "Whether all state group tests passed"
            },
            "timestamp": {
                "type": "string",
                "format": "date-time",
                "description": "When the verification was run"
            },
            "state_groups": {
                "type": "object",
                "properties": {
                    "scrapers": {
                        "type": "object",
                        "properties": {
                            "passed": {"type": "boolean"},
                            "operations": {
                                "type": "object",
                                "properties": {
                                    "set": {"type": "boolean"},
                                    "get": {"type": "boolean"},
                                    "getGroup": {"type": "boolean"},
                                    "delete": {"type": "boolean"}
                                }
                            },
                            "error": {"type": "string"}
                        }
                    },
                    "jobs": {
                        "type": "object",
                        "properties": {
                            "passed": {"type": "boolean"},
                            "operations": {
                                "type": "object",
                                "properties": {
                                    "set": {"type": "boolean"},
                                    "get": {"type": "boolean"},
                                    "getGroup": {"type": "boolean"},
                                    "delete": {"type": "boolean"}
                                }
                            },
                            "error": {"type": "string"}
                        }
                    },
                    "extractions": {
                        "type": "object",
                        "properties": {
                            "passed": {"type": "boolean"},
                            "operations": {
                                "type": "object",
                                "properties": {
                                    "set": {"type": "boolean"},
                                    "get": {"type": "boolean"},
                                    "getGroup": {"type": "boolean"},
                                    "delete": {"type": "boolean"}
                                }
                            },
                            "error": {"type": "string"}
                        }
                    },
                    "content_cache": {
                        "type": "object",
                        "properties": {
                            "passed": {"type": "boolean"},
                            "operations": {
                                "type": "object",
                                "properties": {
                                    "set": {"type": "boolean"},
                                    "get": {"type": "boolean"},
                                    "getGroup": {"type": "boolean"},
                                    "delete": {"type": "boolean"}
                                }
                            },
                            "error": {"type": "string"}
                        }
                    },
                    "monitors": {
                        "type": "object",
                        "properties": {
                            "passed": {"type": "boolean"},
                            "operations": {
                                "type": "object",
                                "properties": {
                                    "set": {"type": "boolean"},
                                    "get": {"type": "boolean"},
                                    "getGroup": {"type": "boolean"},
                                    "delete": {"type": "boolean"}
                                }
                            },
                            "error": {"type": "string"}
                        }
                    }
                }
            },
            "summary": {
                "type": "object",
                "properties": {
                    "total_groups": {"type": "integer"},
                    "passed_groups": {"type": "integer"},
                    "failed_groups": {"type": "integer"}
                }
            }
        },
        "required": ["success", "timestamp", "state_groups", "summary"]
    },
    500: {
        "type": "object",
        "properties": {
            "error": {"type": "string"},
            "details": {"type": "string"}
        },
        "required": ["error"]
    }
}

config = {
    "name": "StateVerification",
    "type": "api",
    "path": "/debug/state-test",
    "method": "GET",
    "description": "Verify all state groups (scrapers, jobs, extractions, content_cache) are working correctly",
    "emits": [],
    "flows": ["debug"],
    "responseSchema": response_schema
}


def generate_test_key() -> str:
    """Generate a unique test key prefixed with _test_ to avoid collision."""
    return f"_test_{uuid.uuid4().hex[:12]}"


async def test_state_group(
    context, 
    group_id: str, 
    test_key: str,
    test_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Test a single state group with all CRUD operations.
    
    Tests:
    1. set() - Store data
    2. get() - Retrieve data and verify it matches
    3. getGroup() - Retrieve all items in group
    4. delete() - Remove test data (cleanup)
    
    Args:
        context: Motia context with state manager
        group_id: The state group to test (e.g., "scrapers")
        test_key: Unique key for this test run
        test_data: Sample data to store and verify
    
    Returns:
        Dictionary with test results for this state group
    """
    result = {
        "passed": False,
        "operations": {
            "set": False,
            "get": False,
            "getGroup": False,
            "delete": False
        },
        "error": None
    }
    
    try:
        # Test 1: SET - Store test data
        await context.state.set(group_id, test_key, test_data)
        result["operations"]["set"] = True
        # context.logger.debug(f"State test: {group_id}.set() passed", {
        #     "group_id": group_id,
        #     "test_key": test_key
        # })
        
        # Test 2: GET - Retrieve and verify data
        retrieved = await context.state.get(group_id, test_key)
        
        # Motia state may wrap data in {"data": ...} format
        actual_data = retrieved
        if isinstance(retrieved, dict) and "data" in retrieved:
            actual_data = retrieved.get("data", retrieved)
        
        # Verify retrieved data matches what we stored
        # We use the _test_key field as the unique verification marker
        if actual_data is not None:
            # First verify our unique test key exists and matches
            stored_test_key = test_data.get("_test_key")
            retrieved_test_key = actual_data.get("_test_key")
            
            if retrieved_test_key == stored_test_key:
                result["operations"]["get"] = True
                # context.logger.debug(f"State test: {group_id}.get() passed", {
                #     "group_id": group_id,
                #     "test_key": test_key,
                #     "_test_key": stored_test_key
                # })
            else:
                result["error"] = f"Data mismatch: _test_key expected '{stored_test_key}', got '{retrieved_test_key}'"
        else:
            result["error"] = f"get() returned None for key that was just set"
        
        # Test 3: GET_GROUP - Retrieve all items in group
        group_items = await context.state.get_group(group_id)
        
        # Verify we got a list back
        if isinstance(group_items, list):
            result["operations"]["getGroup"] = True
            # context.logger.debug(f"State test: {group_id}.get_group() passed", {
            #     "group_id": group_id,
            #     "item_count": len(group_items)
            # })
        else:
            if result["error"] is None:
                result["error"] = f"get_group() returned {type(group_items).__name__} instead of list"
        
        # Test 4: DELETE - Remove test data (cleanup)
        deleted = await context.state.delete(group_id, test_key)
        
        # Verify deletion by trying to get the item again
        post_delete = await context.state.get(group_id, test_key)
        if post_delete is None:
            result["operations"]["delete"] = True
            # context.logger.debug(f"State test: {group_id}.delete() passed", {
            #     "group_id": group_id,
            #     "test_key": test_key
            # })
        else:
            # Some state implementations might return the data wrapper even if empty
            # Check if it's actually empty
            if isinstance(post_delete, dict):
                actual_post_delete = post_delete.get("data", post_delete)
                if actual_post_delete is None:
                    result["operations"]["delete"] = True
                    # context.logger.debug(f"State test: {group_id}.delete() passed", {
                    #     "group_id": group_id,
                    #     "test_key": test_key
                    # })
                else:
                    if result["error"] is None:
                        result["error"] = f"delete() failed - item still exists after deletion"
            else:
                if result["error"] is None:
                    result["error"] = f"delete() failed - item still exists after deletion"
        
        # Mark as passed if all operations succeeded
        all_passed = all(result["operations"].values())
        result["passed"] = all_passed
        
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {str(e)}"
        # context.logger.error(f"State test failed for {group_id}", {
        #     "group_id": group_id,
        #     "error": str(e),
        #     "error_type": type(e).__name__
        # })
    
    return result


async def handler(req: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handler for state verification endpoint.
    
    Tests all four state groups used by Web2API:
    - scrapers: Scraper configurations
    - jobs: Job metadata  
    - extractions: Extraction results
    - content_cache: Cached markdown content
    
    Args:
        req: Request dictionary
        context: Motia context containing state manager and logger
    
    Returns:
        Response dictionary with comprehensive test results
    """
    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        # context.logger.info("Starting state group verification", {
        #     "timestamp": timestamp
        # })
        
        # Generate unique test keys to avoid collisions
        test_suffix = uuid.uuid4().hex[:8]
        
        # Define test data for each state group
        # Note: Use "_test_key" field as unique identifier for verification
        # to avoid conflicts with fields like "data" which might be used by Motia wrapper
        test_configs = {
            "scrapers": {
                "key": f"_test_scr_{test_suffix}",
                "data": {
                    "_test_key": f"_test_scr_{test_suffix}",  # Unique verification field
                    "scraper_id": f"_test_scr_{test_suffix}",
                    "name": "Test Scraper",
                    "description": "State verification test scraper",
                    "schema": {"type": "object", "properties": {"test": {"type": "string"}}},
                    "created_at": timestamp
                }
            },
            "jobs": {
                "key": f"_test_job_{test_suffix}",
                "data": {
                    "_test_key": f"_test_job_{test_suffix}",  # Unique verification field
                    "job_id": f"_test_job_{test_suffix}",
                    "status": "testing",
                    "url": "https://test.example.com",
                    "created_at": timestamp
                }
            },
            "extractions": {
                "key": f"_test_ext_{test_suffix}",
                "data": {
                    "_test_key": f"_test_ext_{test_suffix}",  # Unique verification field
                    "job_id": f"_test_ext_{test_suffix}",
                    "extracted_data": {"test_field": "test_value"},  # Renamed from "data"
                    "url": "https://test.example.com",
                    "completed_at": timestamp
                }
            },
            "content_cache": {
                "key": f"_test_cache_{test_suffix}",
                "data": {
                    "_test_key": f"_test_cache_{test_suffix}",  # Unique verification field
                    "url_hash": f"_test_cache_{test_suffix}",
                    "url": "https://test.example.com",
                    "markdown": "# Test Page\n\nThis is test content.",
                    "cached_at": timestamp
                }
            },
            "monitors": {
                "key": f"_test_mon_{test_suffix}",
                "data": {
                    "_test_key": f"_test_mon_{test_suffix}",  # Unique verification field
                    "monitor_id": f"_test_mon_{test_suffix}",
                    "scraper_id": f"_test_scr_{test_suffix}",
                    "url": "https://test.example.com",
                    "interval_hours": 24,
                    "cron": None,
                    "schedule_type": "interval",
                    "active": True,
                    "last_run": timestamp,
                    "next_run": timestamp,
                    "created_at": timestamp,
                    "updated_at": timestamp
                }
            }
        }
        
        # Run tests for each state group
        state_group_results = {}
        
        for group_id, config in test_configs.items():
            # context.logger.info(f"Testing state group: {group_id}", {
            #     "group_id": group_id,
            #     "test_key": config["key"]
            # })
            
            result = await test_state_group(
                context=context,
                group_id=group_id,
                test_key=config["key"],
                test_data=config["data"]
            )
            
            state_group_results[group_id] = result
            
            # Log result
            if result["passed"]:
                context.logger.info(f"State group {group_id}: ALL TESTS PASSED", {
                    "group_id": group_id,
                    "operations": result["operations"]
                })
            else:
                context.logger.warn(f"State group {group_id}: TESTS FAILED", {
                    "group_id": group_id,
                    "operations": result["operations"],
                    "error": result["error"]
                })
        
        # Calculate summary
        total_groups = len(state_group_results)
        passed_groups = sum(1 for r in state_group_results.values() if r["passed"])
        failed_groups = total_groups - passed_groups
        
        all_passed = passed_groups == total_groups
        
        # context.logger.info("State verification completed", {
        #     "success": all_passed,
        #     "total_groups": total_groups,
        #     "passed_groups": passed_groups,
        #     "failed_groups": failed_groups
        # })
        
        return {
            "status": 200,
            "body": {
                "success": all_passed,
                "timestamp": timestamp,
                "state_groups": state_group_results,
                "summary": {
                    "total_groups": total_groups,
                    "passed_groups": passed_groups,
                    "failed_groups": failed_groups
                }
            }
        }
        
    except Exception as e:
        # context.logger.error("State verification failed - unexpected error", {
        #     "error": str(e),
        #     "error_type": type(e).__name__
        # })
        return {
            "status": 500,
            "body": {
                "error": "State verification failed",
                "details": str(e)
            }
        }

