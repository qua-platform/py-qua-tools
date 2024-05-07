from typing import Union, List

from qiskit.pulse.channels import PulseChannel
from qiskit.pulse.library import Pulse

from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.instruction import Instruction, \
    InstructionContext, TimedInstruction
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.timeline_base import TimelineBase
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.timeline_builder import \
    TimelineBuilder

Element = str
TimelineInstruction = Union[Instruction, InstructionContext]


class TimelineSingleBase(TimelineBase):
    def __init__(self, qubit_index: int, pulse_channel: PulseChannel):
        super().__init__(qubit_index=qubit_index)
        self.instructions: List[TimelineInstruction] = []
        self.pulse_channel: PulseChannel = pulse_channel

    @property
    def current_time(self):
        return self._current_time

    @property
    def current_phase(self):
        return self._current_phase

    @current_time.setter
    def current_time(self, value: int):
        self._current_time = value

    @current_phase.setter
    def current_phase(self, value: float):
        self._current_phase = value

    def is_empty(self):
        return len(self.instructions) == 0

    def is_passive(self):
        from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.delay import Delay
        non_delay_instructions = [
            instr for instr in self.instructions if not isinstance(instr, Delay)
        ]

        return len(non_delay_instructions) == 0

    # def simultaneous(self) -> 'Simultaneous':
    #     from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.simultaneous import \
    #         Simultaneous
    #     simultaneous = Simultaneous(parent_timeline=self)
    #     self.add_instruction(simultaneous)
    #
    #     return simultaneous


class TimelineSingle(TimelineSingleBase, TimelineBuilder):
    def add_instruction(self, instruction: TimelineInstruction):
        """ Sequential behaviour by default. """
        if isinstance(instruction, TimedInstruction):
            self.current_time += instruction.duration
        self.instructions.append(instruction)

    def play(self, duration: int, shape: Pulse, phase: float = 0., limit_amplitude: bool = False, name: str = None):
        from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.play import Play
        self.add_instruction(Play(duration, shape, phase, limit_amplitude, name))

    def reset_phase(self):
        from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.reset_phase import \
            ResetPhase
        self.add_instruction(ResetPhase())

    def delay(self, duration: int):
        from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.delay import Delay
        self.add_instruction(Delay(duration))

    def phase_offset(self, phase: float):
        from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.phase_offset import \
            PhaseOffset
        self.current_phase += phase
        self.add_instruction(PhaseOffset(phase))

    def measure(self):
        from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.measure import Measure
        self.add_instruction(Measure(self.qubit_index))
