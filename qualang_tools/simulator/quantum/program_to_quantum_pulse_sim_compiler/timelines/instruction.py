from dataclasses import dataclass

from qiskit.pulse.channels import PulseChannel

from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.visitors.visitor import Visitor


@dataclass
class Instruction:
    def accept(self, visitor: Visitor, pulse_channel: PulseChannel):
        visitor.visit(self, pulse_channel)


@dataclass
class TimedInstruction(Instruction):
    duration: int


@dataclass
class InstructionContext(Instruction):
    pass
