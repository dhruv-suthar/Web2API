"""
Hash Utilities

Pure utility functions for generating hashes and IDs.
No side effects, no I/O operations.
"""

import uuid
import hashlib


def hash_url(url: str) -> str:
    """
    Hash URL to create a consistent cache/monitor key.
    
    Args:
        url: URL to hash
        
    Returns:
        First 12 characters of SHA256 hash as hexadecimal string
    """
    return hashlib.sha256(url.encode('utf-8')).hexdigest()[:12]


def hash_url_full(url: str) -> str:
    """
    Full SHA256 hash of URL for cache keys.
    
    Args:
        url: URL to hash
        
    Returns:
        Full SHA256 hash as hexadecimal string
    """
    return hashlib.sha256(url.encode('utf-8')).hexdigest()


def generate_job_id() -> str:
    """
    Generate a unique job ID with 'job_' prefix.
    
    Example: job_a1b2c3d4e5f6
    """
    uuid_str = str(uuid.uuid4()).replace("-", "")
    return f"job_{uuid_str[:12]}"


def generate_scraper_id() -> str:
    """
    Generate a unique scraper ID with 'scr_' prefix.
    
    Example: scr_a1b2c3d4e5f6
    """
    uuid_str = str(uuid.uuid4()).replace("-", "")
    return f"scr_{uuid_str[:12]}"


def generate_monitor_id(scraper_id: str, url: str) -> str:
    """
    Generate a unique monitor ID combining scraper_id and url_hash.
    
    Format: {scraper_id}_{url_hash}
    Example: scr_abc123_a1b2c3d4e5f6
    
    Args:
        scraper_id: The scraper identifier
        url: The URL being monitored
        
    Returns:
        Monitor ID string
    """
    url_hash = hash_url(url)
    return f"{scraper_id}_{url_hash}"

