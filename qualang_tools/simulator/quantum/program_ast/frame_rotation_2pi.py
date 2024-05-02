from typing import List

from .node import Node
from .expressions.expression import Expression


class FrameRotation2Pi(Node):
    def __init__(self, phase: Expression, elements: List[str]):
        self.phase = phase
        self.elements = elements