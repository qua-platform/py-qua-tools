from .expressions import Expression
from .node import Node


class Assign(Node):
    def __init__(self, target: str, value: Expression):
        self.target = target
        self.value = value
