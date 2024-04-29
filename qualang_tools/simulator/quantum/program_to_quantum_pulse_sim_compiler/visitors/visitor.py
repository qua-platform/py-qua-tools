import abc

from ...program_ast.node import Node
from ..context import Context


class Visitor(abc.ABC):
    @abc.abstractmethod
    def visit(self, node: Node, context: Context):
        raise NotImplementedError()
