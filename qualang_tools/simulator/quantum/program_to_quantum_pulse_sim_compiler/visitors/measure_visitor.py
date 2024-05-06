from qualang_tools.simulator.quantum.program_ast.measure import Measure
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.context import Context
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.visitors.visitor import Visitor


class MeasureVisitor(Visitor):
    def visit(self, node: Measure, context: Context):
        timeline = context.schedules.get_timeline(node.element)
        timeline.measure()

        context.schedules.restart_schedules_on_same_qubit_as(node.element)
