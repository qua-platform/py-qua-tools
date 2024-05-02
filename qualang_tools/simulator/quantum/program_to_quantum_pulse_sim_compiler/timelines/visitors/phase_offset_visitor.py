from qiskit import pulse
from qiskit.pulse.channels import PulseChannel

from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.phase_offset import PhaseOffset
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.visitors.visitor import Visitor


class PhaseOffsetVisitor(Visitor):
    def visit(self, instruction: PhaseOffset, pulse_channel: PulseChannel):
        pulse.shift_phase(instruction.phase, pulse_channel)
