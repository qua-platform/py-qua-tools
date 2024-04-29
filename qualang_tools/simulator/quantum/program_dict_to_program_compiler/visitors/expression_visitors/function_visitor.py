from .expression_visitor import ExpressionVisitor
from ....program_ast.expressions.function import Function


class FunctionVisitor:
    def visit(self, function: dict) -> Function:
        expression_visitor = ExpressionVisitor()
        arguments = []
        for arg in function['arguments']:
            arguments.append(expression_visitor.visit(arg['scalar']))

        return Function(arguments=arguments,
                        function_name=function['functionName'],
                        library_name=function['libraryName'])
