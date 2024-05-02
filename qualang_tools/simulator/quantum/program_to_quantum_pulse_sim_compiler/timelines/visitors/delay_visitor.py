from qiskit import pulse
from qiskit.pulse.channels import PulseChannel

from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.delay import Delay
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.visitors.visitor import Visitor


class DelayVisitor(Visitor):
    def visit(self, instruction: Delay, pulse_channel: PulseChannel):
        pulse.delay(instruction.duration, pulse_channel)
