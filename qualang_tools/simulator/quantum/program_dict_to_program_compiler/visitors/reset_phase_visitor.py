from typing import List

from .elements import _extract_elements
from .visitor import Visitor
from ...program_ast.reset_phase import ResetPhase
from ...program_ast.node import Node


class ResetPhaseVisitor(Visitor):
    def visit(self, d: dict) -> List[Node]:
        elements = _extract_elements(d)

        return [ResetPhase(elements=elements)]
