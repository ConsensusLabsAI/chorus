"""
Utility functions for the HTN package.
"""

from typing import Any, Dict, List, Union


def my_function(data: Union[str, List[str], Dict[str, Any]]) -> str:
    """A basic utility function.
    
    Args:
        data: Input data of various types
        
    Returns:
        A string representation of the processed data
        
    Raises:
        ValueError: If data is not of a supported type
    """
    if isinstance(data, str):
        return f"String: {data}"
    elif isinstance(data, list):
        return f"List with {len(data)} items: {data}"
    elif isinstance(data, dict):
        return f"Dict with {len(data)} keys: {list(data.keys())}"
    else:
        raise ValueError(f"Unsupported data type: {type(data)}")


def process_numbers(numbers: List[Union[int, float]]) -> Dict[str, Union[int, float]]:
    """Process a list of numbers and return statistics.
    
    Args:
        numbers: List of numbers to process
        
    Returns:
        Dictionary containing count, sum, average, min, and max
        
    Raises:
        ValueError: If the list is empty
    """
    if not numbers:
        raise ValueError("Cannot process empty list")
    
    return {
        "count": len(numbers),
        "sum": sum(numbers),
        "average": sum(numbers) / len(numbers),
        "min": min(numbers),
        "max": max(numbers),
    }


def format_output(data: Any, prefix: str = "Output") -> str:
    """Format data for output with a prefix.
    
    Args:
        data: Data to format
        prefix: Prefix to add to the output
        
    Returns:
        Formatted string
    """
    return f"{prefix}: {data}"
