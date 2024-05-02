from qiskit import pulse
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.phase_offset import PhaseOffset
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.visitors.visitor import Visitor


class PhaseOffsetVisitor(Visitor):
    def visit(self, instruction: PhaseOffset, drive_channel: int):
        pulse.phase_offset(instruction.phase, pulse.DriveChannel(drive_channel))
