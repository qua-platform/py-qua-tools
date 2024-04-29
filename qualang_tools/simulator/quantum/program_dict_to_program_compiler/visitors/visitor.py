import abc
from typing import List

from ...program_ast.node import Node


class Visitor(abc.ABC):
    def __init__(self):
        pass

    @abc.abstractmethod
    def visit(self, d: dict) -> List[Node]:
        raise NotImplementedError()
