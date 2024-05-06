from qualang_tools.simulator.quantum.program_ast.align import Align
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.context import Context
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.visitors.visitor import Visitor


class AlignVisitor(Visitor):
    def visit(self, node: Align, context: Context):
        elements = node.elements
        context.schedules.align(elements)
