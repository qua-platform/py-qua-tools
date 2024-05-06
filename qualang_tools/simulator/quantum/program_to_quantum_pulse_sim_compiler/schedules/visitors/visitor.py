import abc

from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.context import Context


class Visitor(abc.ABC):
    @abc.abstractmethod
    def visit(self, instruction: 'Instruction', instruction_context: Context):
        raise NotImplementedError()
