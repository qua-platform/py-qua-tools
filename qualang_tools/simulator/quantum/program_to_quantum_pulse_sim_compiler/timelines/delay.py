from dataclasses import dataclass

from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.instruction import TimedInstruction


@dataclass
class Delay(TimedInstruction):
    pass
