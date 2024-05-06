from typing import List

from .node import Node
from .program import Program


class For(Program):
    def __init__(self, body: List[Node], cond):
        super().__init__(body)
        self.cond = cond