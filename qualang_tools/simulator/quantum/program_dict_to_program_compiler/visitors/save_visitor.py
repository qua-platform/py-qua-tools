from typing import List

from .visitor import Visitor
from ...program_ast.node import Node


class SaveVisitor(Visitor):
    def visit(self, d: dict) -> List[Node]:
        return []
