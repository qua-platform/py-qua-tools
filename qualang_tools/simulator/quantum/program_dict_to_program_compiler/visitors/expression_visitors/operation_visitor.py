from typing import Literal

from .expression_visitor import ExpressionVisitor
from ....program_ast.expressions.operation import Operation


class OperationVisitor:
    def visit(self, operation: dict) -> Operation:
        expression_visitor = ExpressionVisitor()
        left = expression_visitor.visit(operation['left'])
        right = expression_visitor.visit(operation['right'])
        operation = operation.get('op', 'ADD')

        return Operation(left=left, right=right, operation=operation)
