from dataclasses import dataclass

from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.instruction import TimedInstruction


@dataclass
class Delay(TimedInstruction):
    pass
