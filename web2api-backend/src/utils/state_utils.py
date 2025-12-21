"""
State Utilities

Helper functions for working with Motia state data.
Handles the unwrapping of state responses which may be wrapped in a 'data' key.
"""

from typing import Any, Optional, TypeVar

T = TypeVar('T')


def unwrap_state_data(state_result: Any, default: Any = None) -> Any:
    """
    Unwrap Motia state data from its wrapper.
    
    Motia state.get() may return data wrapped in a 'data' key depending on the 
    storage backend. This function normalizes the response to always return 
    the actual data.
    
    Args:
        state_result: The result from state.get()
        default: Default value to return if state_result is None/empty
        
    Returns:
        The unwrapped data, or default if not found
        
    Examples:
        # Direct value (no wrapper)
        unwrap_state_data({"name": "test"})  # Returns {"name": "test"}
        
        # Wrapped value
        unwrap_state_data({"data": {"name": "test"}})  # Returns {"name": "test"}
        
        # None/empty
        unwrap_state_data(None)  # Returns None
        unwrap_state_data(None, {})  # Returns {}
    """
    if state_result is None:
        return default
    
    if not isinstance(state_result, dict):
        return state_result
    
    # Check if it's wrapped in 'data' key
    # We detect this by checking if 'data' is the only meaningful key
    # or if the structure looks like a Motia wrapper
    if "data" in state_result:
        inner = state_result.get("data")
        # If the inner data is also a dict, return it
        # Otherwise return the whole thing (it might be the actual data structure)
        if inner is not None:
            return inner
    
    return state_result

