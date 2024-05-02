from qualang_tools.simulator.quantum.program_ast.reset_phase import ResetPhase
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.timelines import get_timeline
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.context import Context
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.visitors.visitor import Visitor


class ResetFrameVisitor(Visitor):
    def visit(self, node: ResetPhase, context: Context):
        for element in node.elements:
            timeline = get_timeline(element, context.timelines)
            timeline.phase_offset(-timeline.current_phase)
