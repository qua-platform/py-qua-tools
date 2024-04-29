from typing import Optional

from .expressions.expression import Expression
from .node import Node


class Measure(Node):
    def __init__(self, operation: str, element: str, amp: Optional[Expression] = None):
        self.operation = operation
        self.element = element
        self.amp = amp
