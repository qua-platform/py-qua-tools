from qiskit import pulse
from qiskit.pulse.channels import PulseChannel

from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.play import Play
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.visitors.visitor import Visitor


class PlayVisitor(Visitor):
    def visit(self, instruction: Play, pulse_channel: PulseChannel):
        if instruction.phase == 0.:
            pulse.play(instruction.shape, pulse_channel)
        else:
            with pulse.phase_offset(instruction.phase, pulse_channel):
                pulse.play(instruction.shape, pulse_channel)
