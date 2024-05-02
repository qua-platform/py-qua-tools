from typing import List

from .expression_visitors.expression_visitor import ExpressionVisitor
from .visitor import Visitor
from ...program_ast.align import Align
from ...program_ast.node import Node
from ...program_ast.program_for import For


class ForVisitor(Visitor):
    def visit(self, d: dict) -> List[Node]:
        from .statements_visitor import StatementsVisitor
        statements_visitor = StatementsVisitor()

        cond = ExpressionVisitor().visit(d['condition'])
        init = statements_visitor.visit(d['init'])
        implicit_align = Align(elements=[])
        body = statements_visitor.visit(d['body'])
        update = statements_visitor.visit(d['update'])

        return [*init, For(body=[*body, implicit_align, *update], cond=cond)]
