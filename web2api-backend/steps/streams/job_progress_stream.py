"""
Job Progress Stream

Real-time progress updates for extraction jobs.
Clients can subscribe to this stream to receive live updates on job progress.

Usage:
- Subscribe to groupId: job_id to get updates for a specific job
- The stream provides: status, percent, message, timestamp
"""

# Stream configuration using JSON Schema
config = {
    "name": "jobProgress",
    "schema": {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": "Unique identifier for this stream item (typically same as job_id)"
            },
            "job_id": {
                "type": "string",
                "description": "The job ID this progress update belongs to"
            },
            "status": {
                "type": "string",
                "enum": [
                    "queued",
                    "fetching",
                    "fetched",
                    "extracting",
                    "extracted",
                    "validating",
                    "completed",
                    "failed"
                ],
                "description": "Current status of the extraction job"
            },
            "percent": {
                "type": "integer",
                "minimum": 0,
                "maximum": 100,
                "description": "Progress percentage (0-100)"
            },
            "message": {
                "type": "string",
                "description": "Optional human-readable status message"
            },
            "timestamp": {
                "type": "string",
                "format": "date-time",
                "description": "When this update was recorded"
            }
        },
        "required": ["id", "status", "percent"]
    },
    "baseConfig": {
        "storageType": "default"
    }
}

