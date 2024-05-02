from qiskit import pulse
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.measure import (Measure)
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.visitors.visitor import Visitor


class MeasureVisitor(Visitor):
    def visit(self, instruction: Measure, drive_channel: int):
        # pulse.acquire(1, 0, pulse.MemorySlot(drive_channel))
        pulse.measure(instruction.qubit_index, pulse.MemorySlot(instruction.qubit_index))
