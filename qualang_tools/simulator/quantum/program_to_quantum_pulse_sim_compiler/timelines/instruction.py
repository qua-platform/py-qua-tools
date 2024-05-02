from dataclasses import dataclass

from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.visitors.visitor import Visitor


@dataclass
class Instruction:
    def accept(self, visitor: Visitor, drive_channel: int):
        visitor.visit(self, drive_channel)


@dataclass
class TimedInstruction(Instruction):
    duration: int


@dataclass
class InstructionContext(Instruction):
    pass
