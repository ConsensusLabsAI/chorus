"""
Core functionality for the HTN package.
"""

from typing import Any, Dict, List, Optional


class MyClass:
    """A basic example class."""
    
    def __init__(self, name: str, value: Optional[Any] = None):
        """Initialize the class.
        
        Args:
            name: The name of the instance
            value: An optional value to store
        """
        self.name = name
        self.value = value
        self._data: Dict[str, Any] = {}
    
    def add_data(self, key: str, value: Any) -> None:
        """Add data to the instance.
        
        Args:
            key: The key to store the value under
            value: The value to store
        """
        self._data[key] = value
    
    def get_data(self, key: str) -> Optional[Any]:
        """Get data from the instance.
        
        Args:
            key: The key to retrieve
            
        Returns:
            The value associated with the key, or None if not found
        """
        return self._data.get(key)
    
    def list_keys(self) -> List[str]:
        """List all keys in the data store.
        
        Returns:
            A list of all keys
        """
        return list(self._data.keys())
    
    def __str__(self) -> str:
        """String representation of the instance."""
        return f"MyClass(name='{self.name}', value={self.value})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the instance."""
        return f"MyClass(name='{self.name}', value={self.value}, data={self._data})"
