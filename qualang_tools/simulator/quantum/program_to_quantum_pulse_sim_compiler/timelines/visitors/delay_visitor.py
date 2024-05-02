from qiskit import pulse
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.delay import Delay
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.visitors.visitor import Visitor


class DelayVisitor(Visitor):
    def visit(self, instruction: Delay, drive_channel: int):
        pulse.delay(instruction.duration, pulse.DriveChannel(drive_channel))
