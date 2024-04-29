from qualang_tools.simulator.quantum.program_ast.measure import Measure
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.context import Context
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines import Timeline, get_timeline, restart_qubit_timelines
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.visitors.visitor import Visitor


class MeasureVisitor(Visitor):
    def visit(self, node: Measure, context: Context):
        e = node.element
        timeline = get_timeline(e, context.timelines)
        timeline.add_instruction('acquire', 1)

        restart_qubit_timelines(e, context.timelines)
