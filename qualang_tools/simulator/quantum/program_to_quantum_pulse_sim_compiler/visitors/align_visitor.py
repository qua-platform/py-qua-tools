from typing import List

from qualang_tools.simulator.quantum.program_ast.align import Align
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.context import Context
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.timelines import Timeline
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.visitors.visitor import Visitor


def align(timelines: List[Timeline]):
    latest_time = 0
    for timeline in timelines:
        latest_time = max(latest_time, timeline.current_time)

    for timeline in timelines:
        time_delta = latest_time - timeline.current_time
        if time_delta != 0:
            timeline.delay(time_delta)


class AlignVisitor(Visitor):
    def visit(self, node: Align, context: Context):
        timelines = [context.timelines[e][-1] for e in node.elements]
        align(timelines)
