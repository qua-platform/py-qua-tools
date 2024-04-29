from typing import List

from .elements import _extract_elements
from .visitor import Visitor
from ...program_ast.align import Align
from ...program_ast.node import Node


class AlignVisitor(Visitor):
    def visit(self, d: dict) -> List[Node]:
        elements = _extract_elements(d)

        return [Align(elements=elements)]
