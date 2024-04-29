from typing import List, Optional

from .expressions.definition import Definition
from .node import Node


class Program(Node):
    def __init__(self, body: List[Node], vars: Optional[List[Definition]] = None):
        self.body = body
        self.vars = vars if vars is not None else []
