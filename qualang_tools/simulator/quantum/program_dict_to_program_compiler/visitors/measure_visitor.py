from typing import List

from .expression_visitors.expression_visitor import ExpressionVisitor
from .visitor import Visitor
from ...program_ast.measure import Measure
from ...program_ast.node import Node


class MeasureVisitor(Visitor):
    def visit(self, d: dict) -> List[Node]:
        element = d['qe']['name']
        operation = d['pulse']['name']
        amp = None
        if 'amp' in d:
            amp = ExpressionVisitor().visit(d['amp']['v0'])

        return [Measure(operation=operation, element=element, amp=amp)]
