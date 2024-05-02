import abc


class Visitor(abc.ABC):
    @abc.abstractmethod
    def visit(self, instruction: 'Instruction', drive_channel: int):
        raise NotImplementedError()
