from .definition_visitor import DefinitionVisitor
from .node_visitor import NodeVisitor
from ..context import Context
from ...program_ast.program import Program


class ProgramVisitor:
    def visit(self, program: Program, context: Context):
        for definition in program.vars:
            var = DefinitionVisitor().visit(definition)
            context.vars.update(var)

        node_visitor = NodeVisitor()
        for node in program.body:
            node.accept(node_visitor, context)

        return None
