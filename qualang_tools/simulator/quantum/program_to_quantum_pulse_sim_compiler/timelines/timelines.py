from typing import List, Dict, Union

from qiskit.pulse.library import Pulse

from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.delay import Delay
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.instruction import Instruction, \
    TimedInstruction, InstructionContext
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.measure import Measure
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.phase_offset import PhaseOffset
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.play import Play

Element = str
TimelineInstruction = Union[Instruction, InstructionContext]


class TimelineInstructionBuilder:
    def __init__(self):
        self.current_time: float = 0
        self.instructions: List[TimelineInstruction] = []

    def add_instruction(self, instruction: TimelineInstruction):
        """ Sequential behaviour by default. """
        if isinstance(instruction, TimedInstruction):
            self.current_time += instruction.duration
        self.instructions.append(instruction)

    def play(self, duration: int, shape: Pulse, phase: float = 0., limit_amplitude: bool = False):
        self.add_instruction(Play(duration, shape, phase, limit_amplitude))

    def delay(self, duration: int):
        self.add_instruction(Delay(duration))

    def phase_offset(self, phase: float):
        self.add_instruction(PhaseOffset(phase))


class Timeline(TimelineInstructionBuilder):
    def __init__(self, qubit_index: int, drive_channel: int):
        super().__init__()
        self.qubit_index: int = qubit_index
        self.drive_channel: int = drive_channel

    def measure(self):
        self.add_instruction(Measure(self.qubit_index))

    def simultaneous(self) -> 'Simultaneous':
        from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.simultaneous import \
            Simultaneous
        simultaneous = Simultaneous(parent_timeline=self)
        self.add_instruction(simultaneous)

        return simultaneous


Timelines = Dict[Element, List[Timeline]]


def get_timeline(element: str, timelines: Timelines):
    return timelines[element][-1]
