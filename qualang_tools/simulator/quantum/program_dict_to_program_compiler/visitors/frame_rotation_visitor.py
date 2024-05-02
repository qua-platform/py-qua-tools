from typing import List

from .elements import _extract_elements
from .expression_visitors.expression_visitor import ExpressionVisitor
from .visitor import Visitor
from ...program_ast.frame_rotation_2pi import FrameRotation2Pi
from ...program_ast.node import Node


class FrameRotationVisitor(Visitor):
    def visit(self, d: dict) -> List[Node]:
        phase = ExpressionVisitor().visit(d['value'])
        elements = _extract_elements(d)

        return [FrameRotation2Pi(phase=phase, elements=elements)]
