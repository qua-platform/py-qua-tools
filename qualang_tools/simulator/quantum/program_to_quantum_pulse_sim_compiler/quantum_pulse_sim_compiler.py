import qm
from qiskit_dynamics import DynamicsBackend
from qiskit import pulse

from .context import Context
from .quantum_pulse_sim import QuantumPulseSimulator
from .visitors.instruction_visitor import InstructionVisitor
from ..program_dict_to_program_compiler.program_tree_builder import ProgramTreeBuilder
from .visitors.program_visitor import ProgramVisitor


class Compiler:
    def __init__(self, config: dict):
        self.config = config

    def compile(self, program: qm.Program, backend: DynamicsBackend) -> QuantumPulseSimulator:
        # build a Program AST using the raw QUA program dictionary
        program_tree = ProgramTreeBuilder().build(program)

        # compile the program AST into a runnable qiskit pulse simulator
        context = Context(self.config)
        program_tree.accept(ProgramVisitor(), context)

        timeline_lengths = [len(timeline) for timeline in context.timelines.values()]
        assert all([length / timeline_lengths[0] == 1 for length in timeline_lengths])

        schedules = []
        instruction_visitor = InstructionVisitor()
        for i in range(timeline_lengths[0]):
            with pulse.build() as schedule:
                for timelines in context.timelines.values():
                    with pulse.align_sequential():
                        for instruction in timelines[i].instructions:
                            instruction_visitor.visit(instruction, timelines[i].drive_channel)

            if len(schedule) > 0:
                schedules.append(schedule)

        sim = QuantumPulseSimulator(backend, schedules)

        return sim