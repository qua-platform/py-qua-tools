from typing import List

from .node import Node


class ResetFrame(Node):
    def __init__(self, elements: List[str]):
        self.elements = elements
