from dataclasses import dataclass

from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.timeline_single import \
    TimelineSingle


@dataclass
class Context:
    timeline: TimelineSingle
