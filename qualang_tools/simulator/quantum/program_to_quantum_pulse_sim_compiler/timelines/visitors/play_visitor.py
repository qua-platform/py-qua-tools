from qiskit import pulse
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.play import Play
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.visitors.visitor import Visitor


class PlayVisitor(Visitor):
    def visit(self, instruction: Play, drive_channel: int):
        drive_channel = pulse.DriveChannel(drive_channel)
        if instruction.phase == 0.:
            pulse.play(instruction.shape, drive_channel)
        else:
            with pulse.phase_offset(instruction.phase, drive_channel):
                pulse.play(instruction.shape, drive_channel)
