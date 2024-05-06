from typing import List

from .expression_visitors.expression_visitor import ExpressionVisitor
from .visitor import Visitor
from ...program_ast._if import If
from ...program_ast.node import Node


class IfVisitor(Visitor):
    def visit(self, d: dict) -> List[Node]:
        from .statements_visitor import StatementsVisitor
        statements_visitor = StatementsVisitor()

        cond = ExpressionVisitor().visit(d['condition'])
        body = statements_visitor.visit(d['body'])

        return [If(body=[*body], cond=cond)]
