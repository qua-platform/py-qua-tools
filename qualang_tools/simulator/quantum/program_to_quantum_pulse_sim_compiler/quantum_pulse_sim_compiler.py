import qm
from qiskit_dynamics import DynamicsBackend

from .program_to_timeline_compiler import ProgramToTimelineCompiler
from .quantum_pulse_sim import QuantumPulseSimulator
from .timeline_to_schedule_compiler import TimelineToPulseScheduleCompiler
from ..architectures.transmon_pair_backend_from_qua import ConfigToTransmonPairBackendMap
from ..program_dict_to_program_compiler.program_tree_builder import ProgramTreeBuilder


class Compiler:
    def __init__(self, config: dict):
        self.config = config

    def compile(self,
                program: qm.Program,
                channel_map: ConfigToTransmonPairBackendMap,
                backend: DynamicsBackend) -> QuantumPulseSimulator:

        # Compile raw program dictionary into an abstract syntax tree
        program_tree = ProgramTreeBuilder().build(program)

        # Compile the abstract syntax tree into an intermediate, pulse timeline representation
        timelines = ProgramToTimelineCompiler().compile(self.config, program_tree, channel_map)

        # Compile the pulse timelines into qiskit.pulse schedules
        schedules = TimelineToPulseScheduleCompiler().compile(timelines, backend)

        # Encapsulate pulse schedules and backend in simulator object
        sim = QuantumPulseSimulator(backend, schedules)

        return sim
