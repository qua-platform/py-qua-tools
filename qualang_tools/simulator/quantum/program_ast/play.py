from typing import List, Optional

from .expressions import Expression
from .node import Node


class Play(Node):
    def __init__(self, operation: str, element: str, amp: Optional[Expression] = None, duration: Optional[Expression] = None):
        self.operation = operation
        self.element = element
        self.amp = amp
        self.duration = duration
