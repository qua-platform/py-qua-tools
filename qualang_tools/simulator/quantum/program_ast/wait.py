from typing import List

from .node import Node
from .expressions.expression import Expression


class Wait(Node):
    def __init__(self, time: Expression, elements: List[str]):
        self.time = time
        self.elements = elements