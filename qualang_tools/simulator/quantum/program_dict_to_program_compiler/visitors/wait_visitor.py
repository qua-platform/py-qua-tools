from typing import List

from .elements import _extract_elements
from .expression_visitors.expression_visitor import ExpressionVisitor
from .visitor import Visitor
from ...program_ast.node import Node
from ...program_ast.wait import Wait


class WaitVisitor(Visitor):
    def visit(self, d: dict) -> List[Node]:
        assert len(d['time'].keys()) == 1
        time = ExpressionVisitor().visit(d['time'])
        elements = _extract_elements(d)

        return [Wait(time=time, elements=elements)]
