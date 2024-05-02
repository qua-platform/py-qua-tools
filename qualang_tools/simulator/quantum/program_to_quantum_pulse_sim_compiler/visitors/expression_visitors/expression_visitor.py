from ...context import Context
from ....program_ast.expressions import Expression, Reference, Operation, Literal, Function


class ExpressionVisitor:
    def visit(self, expression: Expression, context: Context):
        if isinstance(expression, Operation):
            # local import to avoid circular import
            from .operation_visitor import OperationVisitor
            return OperationVisitor().visit(expression, context)

        elif isinstance(expression, Reference):
            return context.vars[expression.name]

        elif isinstance(expression, Literal):
            return eval(expression.value)

        elif isinstance(expression, Function):
            from .function_visitor import FunctionVisitor
            return FunctionVisitor().visit(expression, context)

        else:
            raise NotImplementedError(f"Uncrecognised expression type {type(expression)}")
