from dataclasses import dataclass

from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.instruction import \
    InstructionContext, Instruction, TimedInstruction
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.timelines import \
    TimelineSingleBase
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.timeline_single import \
    TimelineSingle
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.visitors.visitor import Visitor


class Simultaneous(TimelineSingle):
    def __init__(self, parent_timeline: TimelineSingleBase):
        super().__init__()
        self.parent_timeline: TimelineSingleBase = parent_timeline

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
