from typing import List

from .expression_visitors.expression_visitor import ExpressionVisitor
from .visitor import Visitor
from ...program_ast.node import Node
from ...program_ast.program_for import For


class StrictTimingVisitor(Visitor):
    def visit(self, d: dict) -> List[Node]:
        from .statements_visitor import StatementsVisitor
        statements_visitor = StatementsVisitor()

        return statements_visitor.visit(d['body'])
