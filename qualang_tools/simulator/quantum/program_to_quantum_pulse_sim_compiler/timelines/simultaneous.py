from dataclasses import dataclass

from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.instruction import \
    InstructionContext, Instruction, TimedInstruction
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.timelines import \
    TimelineInstructionBuilder, Timeline
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.visitors.visitor import Visitor


class Simultaneous(TimelineInstructionBuilder):
    def __init__(self, parent_timeline: Timeline):
        super().__init__()
        self.parent_timeline: Timeline = parent_timeline

    def accept(self, visitor: Visitor, drive_channel: int):
        visitor.visit(self, drive_channel)

    def add_instruction(self, instruction: Instruction):
        if isinstance(instruction, TimedInstruction):
            if len(self.instructions) > 0:
                durations = [i.duration for i in self.instructions if isinstance(i, TimedInstruction)]
                updated_current_time = max([instruction.duration, *durations])
                update_amount = self.current_time - updated_current_time
                self.current_time = updated_current_time
                self.parent_timeline.current_time += update_amount
            else:
                self.current_time = instruction.duration
                self.parent_timeline.current_time += instruction.duration

        self.instructions.append(instruction)
