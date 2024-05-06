from typing import Literal

from qualang_tools.simulator.quantum.program_ast.expressions import Operation
from .expression_visitor import ExpressionVisitor
from ...context import Context


def _attempt_early_exit(left, op: str):
    if left == 0 and op == 'MULT':
        return 0
    return None


class OperationVisitor:
    def visit(self, operation: Operation, context: Context):
        op = operation.operation

        expression_visitor = ExpressionVisitor()

        left = expression_visitor.visit(operation.left, context=context)

        early_exit_attempt = _attempt_early_exit(left, op)
        if early_exit_attempt is not None:
            return early_exit_attempt

        right = expression_visitor.visit(operation.right, context=context)

        if op == 'ADD':
            return left + right
        elif op == 'DIV':
            return left / right
        elif op == 'MULT':
            return left * right
        elif op == 'SHR':
            return left >> right
        elif op == 'GT':
            return left > right
        elif op == 'GET':
            return left >= right
        elif op == 'LT':
            return left < right
        elif op == 'LET':
            return left <= right
        elif op == 'EQ':
            return left == right
        else:
            raise NotImplementedError(f'Unrecognised operation {op}')
