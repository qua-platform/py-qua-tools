from ....program_ast.expressions.expression import Expression
from ....program_ast.expressions.literal import Literal
from ....program_ast.expressions.reference import Reference


class ExpressionVisitor:
    def visit(self, expression: dict) -> Expression:
        assert len(expression.keys()) == 1
        expression_type = list(expression.keys())[0]

        if expression_type == 'literal':
            return Literal(value=expression['literal']['value'])

        elif expression_type == 'binaryOperation':
            # local import to avoid circular import
            from .operation_visitor import OperationVisitor
            return OperationVisitor().visit(expression['binaryOperation'])

        elif expression_type == 'variable':
            return Reference(expression['variable']['name'])

        elif expression_type == 'scalar':
            return Reference(expression['scalar']['name'])

        elif expression_type == 'libFunction':
            # local import to avoid circular import
            from .function_visitor import FunctionVisitor
            return FunctionVisitor().visit(expression['libFunction'])

        else:
            raise NotImplementedError(f'Unknown expression type {expression_type}')
