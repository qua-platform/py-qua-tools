from dataclasses import dataclass

from qiskit.pulse.library import Pulse

from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.instruction import TimedInstruction


@dataclass
class Play(TimedInstruction):
    shape: Pulse
    phase: float = 0.
    limit_amp: bool = False
    name: str = None
