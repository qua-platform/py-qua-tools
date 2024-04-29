import qm

from ..program_ast.program import Program
from .visitors.program_visitor import ProgramVisitor


class ProgramTreeBuilder:
    def __init__(self):
        pass

    def build(self, program: qm.Program) -> Program:
        program_body = program

        visitor = ProgramVisitor()
        return visitor.visit(program_body)
