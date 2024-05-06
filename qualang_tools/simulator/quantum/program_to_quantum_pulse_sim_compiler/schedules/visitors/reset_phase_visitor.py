from qiskit import pulse

from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.context import Context
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.phase_offset import PhaseOffset
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.visitors.visitor import Visitor


class ResetPhaseVisitor(Visitor):
    def visit(self, instruction: PhaseOffset, instruction_context: Context):
        pulse.set_phase(0, instruction_context.timeline.pulse_channel)
