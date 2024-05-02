from qiskit import pulse
from qiskit.pulse.channels import PulseChannel

from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.measure import (Measure)
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.visitors.visitor import Visitor


class MeasureVisitor(Visitor):
    def visit(self, instruction: Measure, pulse_channel: PulseChannel):
        pulse.measure(
            qubits=instruction.qubit_index,
            registers=pulse.MemorySlot(instruction.qubit_index)
        )
