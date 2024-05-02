from typing import Literal

from qualang_tools.simulator.quantum.program_ast.expressions import Operation, Function
from .expression_visitor import ExpressionVisitor
from ...context import Context


class FunctionVisitor:
    def visit(self, function: Function, context: Context):
        expression_visitor = ExpressionVisitor()
        if function.function_name == 'mul_fixed_by_int':
            left = expression_visitor.visit(function.arguments[0], context)
            right = expression_visitor.visit(function.arguments[1], context)
            return _mul_fixed_by_int(left, right)
        else:
            raise NotImplementedError(f"Unimplemented function {function.function_name}.")
        pass


def _mul_fixed_by_int(left: float, right: int) -> float:
    return left * right
