import abc

from qiskit.pulse.channels import PulseChannel


class Visitor(abc.ABC):
    @abc.abstractmethod
    def visit(self, instruction: 'Instruction', pulse_channel: PulseChannel):
        raise NotImplementedError()
