from typing import List

from .expression_visitors.expression_visitor import ExpressionVisitor
from .visitor import Visitor
from ...program_ast.play import Play
from ...program_ast.node import Node


class PlayVisitor(Visitor):
    def visit(self, d: dict) -> List[Node]:
        operation = d['namedPulse']['name']
        element = d['qe']['name']

        amp = None
        if 'amp' in d:
            amp = ExpressionVisitor().visit(d['amp']['v0'])

        duration = None
        if 'duration' in d:
            duration = ExpressionVisitor().visit(d['duration'])

        for k in d:
            if k not in ['loc', 'qe', 'namedPulse', 'amp', 'duration']:
                raise NotImplementedError(f"Unhandled play parameter {k}")

        return [Play(operation, element, amp, duration)]
