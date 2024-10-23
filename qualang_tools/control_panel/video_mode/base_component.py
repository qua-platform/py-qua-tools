from abc import ABC
from typing import Dict, Any, List, Tuple, Callable

class DashComponent(ABC):
    """Base class for components that have Dash UI elements."""
    
    def __init__(self, component_id: str):
        self.component_id = component_id
    
    def get_component_id(self, suffix: str) -> str:
        """Get the full component ID for a given suffix."""
        return f"{self.component_id}-{suffix}"
    
    def get_dash_components(self) -> List[Any]:
        """Return a list of Dash components specific to this component."""
        return []
    
    def get_callbacks(self) -> List[Tuple[str, Callable]]:
        """Return a list of (pattern, callback) tuples for this component."""
        return []
    
    def update_from_inputs(self, inputs: Dict[str, Any]):
        """Update component attributes based on input values."""
        pass
