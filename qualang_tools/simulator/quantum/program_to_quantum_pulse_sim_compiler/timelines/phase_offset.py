from dataclasses import dataclass

from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.instruction import Instruction


@dataclass
class PhaseOffset(Instruction):
    phase: float
