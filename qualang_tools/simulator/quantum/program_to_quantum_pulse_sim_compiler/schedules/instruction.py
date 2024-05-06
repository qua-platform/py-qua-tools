from dataclasses import dataclass


@dataclass
class Instruction:
    def accept(self, visitor: 'Visitor', instruction_context: 'Context'):
        visitor.visit(self, instruction_context)


@dataclass
class TimedInstruction(Instruction):
    duration: int


@dataclass
class InstructionContext(Instruction):
    pass
