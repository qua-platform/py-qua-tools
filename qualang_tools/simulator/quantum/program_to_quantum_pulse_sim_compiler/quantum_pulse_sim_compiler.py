import qm
from qiskit_dynamics import DynamicsBackend
from qiskit import pulse

from .context import Context
from .quantum_pulse_sim import QuantumPulseSimulator
from .timelines.timeline_compiler import TimelineCompiler
from ..architectures.transmon_pair_backend_from_qua import ConfigToTransmonPairBackendMap
from ..program_dict_to_program_compiler.program_tree_builder import ProgramTreeBuilder
from .visitors.program_visitor import ProgramVisitor


class Compiler:
    def __init__(self, config: dict):
        self.config = config

    def compile(self, program: qm.Program, map: ConfigToTransmonPairBackendMap, backend: DynamicsBackend) -> QuantumPulseSimulator:
        # build a Program AST using the raw QUA program dictionary
        program_tree = ProgramTreeBuilder().build(program)

        # compile the program AST into a runnable qiskit pulse simulator
        context = Context(self.config, map)
        program_tree.accept(ProgramVisitor(), context)

        schedules = TimelineCompiler().compile(context.timelines, backend)

        sim = QuantumPulseSimulator(backend, schedules)

        return sim
