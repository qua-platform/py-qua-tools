from qiskit.pulse.channels import PulseChannel

from qualang_tools.config import Pulse
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.timeline_base import TimelineBase
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.timeline_builder import \
    TimelineBuilder
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.timeline_single import \
    TimelineSingle


class TimelineIQBase(TimelineBase):
    def __init__(self, qubit_index: int, pulse_channel_i: PulseChannel, pulse_channel_q: PulseChannel):
        super().__init__(qubit_index)
        self.I = TimelineSingle(qubit_index=qubit_index, pulse_channel=pulse_channel_i)
        self.Q = TimelineSingle(qubit_index=qubit_index, pulse_channel=pulse_channel_q)

    @property
    def current_phase(self):
        return self.I.current_phase

    @property
    def current_time(self):
        return self.I.current_time


class TimelineIQ(TimelineIQBase, TimelineBuilder):
    def play_i(self, duration: int, shape: Pulse, phase: float = 0., limit_amplitude: bool = False, name: str = None):
        self.I.play(duration, shape, phase, limit_amplitude, name)

    def play_q(self, duration: int, shape: Pulse, phase: float = 0., limit_amplitude: bool = False, name: str = None):
        self.Q.play(duration, shape, phase, limit_amplitude, name)

    def reset_phase(self):
        self.I.reset_phase()
        self.Q.reset_phase()

    def delay(self, duration: int):
        self.I.delay(duration)
        self.Q.delay(duration)

    def phase_offset(self, phase: float):
        self.I.phase_offset(phase)
        self.Q.phase_offset(phase)

    def is_passive(self):
        return self.I.is_passive() and self.Q.is_passive()

    def is_empty(self):
        return self.I.is_empty() and self.Q.is_empty()
