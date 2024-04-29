from typing import List

from .expression_visitors.expression_visitor import ExpressionVisitor
from ...program_ast.assign import Assign
from ...program_ast.node import Node
from .visitor import Visitor


class AssignVisitor(Visitor):
    def visit(self, d: dict) -> List[Node]:
        target = d['target']['variable']['name']
        value = ExpressionVisitor().visit(d['expression'])

        return [Assign(target, value)]
