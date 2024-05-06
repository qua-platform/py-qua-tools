from typing import Union

from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.timeline_IQ import TimelineIQ
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.timeline_single import \
    TimelineSingle

Timeline = Union[TimelineSingle, TimelineIQ]
