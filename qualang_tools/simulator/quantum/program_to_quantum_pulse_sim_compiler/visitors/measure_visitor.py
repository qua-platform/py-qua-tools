from qualang_tools.simulator.quantum.program_ast.measure import Measure
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.context import Context
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.timelines import get_timeline, \
    Timelines, Timeline
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.visitors.visitor import Visitor


class MeasureVisitor(Visitor):
    def visit(self, node: Measure, context: Context):
        e = node.element
        timeline = get_timeline(e, context.timelines)
        timeline.measure()

        restart_qubit_timelines(e, context.timelines)


def restart_qubit_timelines(element: str, timelines: Timelines):
    qubit_index = get_timeline(element, timelines).qubit_index
    for timeline in timelines.values():
        if timeline[-1].qubit_index == qubit_index:
            timeline.append(Timeline(
                qubit_index=qubit_index,
                drive_channel=timeline[-1].drive_channel
            ))

