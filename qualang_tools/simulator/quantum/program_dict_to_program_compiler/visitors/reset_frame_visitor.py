from typing import List

from .elements import _extract_elements
from .visitor import Visitor
from ...program_ast.reset_frame import ResetFrame
from ...program_ast.node import Node


class ResetFrameVisitor(Visitor):
    def visit(self, d: dict) -> List[Node]:
        elements = _extract_elements(d)

        return [ResetFrame(elements=elements)]
